// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/interfaces/KeeperCompatibleInterface.sol";
import "contracts/ErstwhileHeros.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/** @title ErstwhileHerosNFT
 *   @notice Contract to manage all transaction related to NFT Market place
 *   @author Prashantha M
 */
contract ErstwhileHerosNFT is
    ERC1155, 
    Ownable,
    VRFConsumerBaseV2,
    KeeperCompatibleInterface
{
    // Chainlink VRF Variables
    VRFCoordinatorV2Interface private immutable i_vrfCoordinator;
    uint64 private immutable i_subscriptionId;
    bytes32 private immutable i_gasLane;
    uint32 private immutable i_callbackGasLimit;
    uint16 private constant REQUEST_CONFIRMATIONS = 3;
    event RequestedRandomness(bytes32 requestId);

    enum NFT_STATE {
        OPEN,
        CLOSED
    }

    enum TRAN_TYPE {
        OFFERER_ADDED,
        NFT_MINTED,
        WITHDWAR
    }

    struct NFTItem {
        uint256 tokenId;
        string tokenName;
        string tokenURI;
        address payable issuer;
        uint256 quantity;
        uint256 price;
        uint256 nftPostedTimeStamp;
        string imgUrl;
        NFT_STATE nftState;
    }
    //uint256[] public s_randomWords;

    //events
    event NFTListed(uint256 tokenId, string tokenName, string tokenURI, address issuer, uint256 quantity, uint256 price, uint256 nftPostedTimeStamp, string imgUrl, NFT_STATE state);
    event NewOffererAdded(uint256 tokenId, address offerer);
    event NFTMinted(uint256 tokenId, uint256 quantity, address offerer);
    event NFTClosed(uint256 tokenId, uint256 originalQuantity, uint256 totalOffers);
    event Withdraw(address issuer, uint256 tokenId, uint256 amount);
    event NFTTransactions(address eventUser, uint256 tokenId, TRAN_TYPE eventType);
    event ethTransferred(address receiver, uint256 tokenId, uint256 amount);

    ErstwhileHeros erstwhileHeros;

    mapping(uint256 => NFTItem) ListedNFTs; //All NFTs
    uint256[] tokenIDs; //All token Ids
    mapping(uint256 => mapping(address => uint256)) private tokenBalance; //Mapping token -> owner{Hero/Buyer} -> tokane count
    mapping(uint256 => uint256) private ethBalance; //Mapping token -> ethBalance
    mapping(uint256 => address[]) private NFTOffers; //tokenID -> offerers - For each token, list of offerers

    uint32 private currentActiveNFTs; //current active NFTs
    uint256[] private currentClosingNFTs; //Closing NFTs today
    address[] private OfferersOffered; //Used for refund -- Refund all offerers who are not in this list for -- per token Id
    uint256 private immutable nftInterval; //NFT interval -- Fixed currently

    constructor(address _erstwhileHeros, uint256 interval, address vrfCoordinatorV2, uint64 subscriptionId, bytes32 gasLane, uint32 callbackGasLimit)
        ERC1155("https://gateway.pinata.cloud/ipfs/{CID}")
        VRFConsumerBaseV2(vrfCoordinatorV2)
    {
        erstwhileHeros = ErstwhileHeros(_erstwhileHeros);
        i_vrfCoordinator = VRFCoordinatorV2Interface(vrfCoordinatorV2);
        i_gasLane = gasLane;
        i_subscriptionId = subscriptionId;
        i_callbackGasLimit = callbackGasLimit;
        nftInterval = interval;

        //s_randomWords.push(4242);
        //s_randomWords.push(6245);
        //s_randomWords.push(5245);
    }

    function addToken(uint256 _tokenId, string memory _tokenName, string memory _tokenURI, uint256 _quantity, uint256 _price, string memory _imgUrl
    ) external returns (uint256) {
        require(isValidHero(msg.sender) == true, "Invalid Hero");
        require(ListedNFTs[_tokenId].issuer == address(0), "Token exists");

        ListedNFTs[_tokenId] = NFTItem(_tokenId, _tokenName, _tokenURI, payable(msg.sender), _quantity, _price, block.timestamp, _imgUrl, NFT_STATE.OPEN);

        emit NFTListed(_tokenId, _tokenName, _tokenURI, msg.sender, _quantity, _price, block.timestamp, _imgUrl, NFT_STATE.OPEN);

        tokenIDs.push(_tokenId);
        tokenBalance[_tokenId][msg.sender] = _quantity;
        currentActiveNFTs++;
        return _tokenId;
    }

    function addNFTOffer(uint256 _tokenId) external payable {
        //checking to see if token exists by looking at NFT issuer address
        require(isValidToken(_tokenId) == true,"Invalid token");
        //Ensuring issuer doesn't put themself on the offer
        require(ListedNFTs[_tokenId].issuer != msg.sender,"Invalid Offerer");
        //Ensuring listed NFT has quantity more than zero
        require(ListedNFTs[_tokenId].quantity > 0,"NFT has zero quantity");
        //Offer duplicate check
        require(offererExists(_tokenId, msg.sender) == false,"Duplicate offer");
        //NFT is still OPEN
        require(ListedNFTs[_tokenId].nftState == NFT_STATE.OPEN,"NFT closed");
        //Ensure price is sent as well
        require(msg.value >= ListedNFTs[_tokenId].price,"Need price");

        //Get the price and take the approval for future transaction
        uint256 nftPrice = ListedNFTs[_tokenId].price;
        ethBalance[_tokenId] += nftPrice;
        //erc20Token.approve(owner, nftPrice);

        //Update the contract with offer and quantity
        NFTOffers[_tokenId].push(payable(msg.sender));
        //tokenOfferQuntity[_tokenId]++;
        emit NewOffererAdded(_tokenId, msg.sender);
        emit NFTTransactions(msg.sender, _tokenId, TRAN_TYPE.OFFERER_ADDED);

    }

    function offererExists(uint256 _tokenId, address _offerer) public view returns (bool) {
        for (uint256 i = 0; i < NFTOffers[_tokenId].length; i++) {
            if (NFTOffers[_tokenId][i] == _offerer) return true;
        }
        return false;
    }

    // @dev This is the function that the Chainlink Keeper nodes call they look for `upkeepNeeded` to return True.
    function checkUpkeep(bytes memory /* checkData */)
        public view override returns (bool upkeepNeeded, bytes memory /* performData */) {
        bool isOpen = (currentActiveNFTs > 0);
        bool timePassed = false;
        //bool hasOfferers = false; -- IMPORTANT - Commented as even if there are no offer and time has passed, need to do clean up.

        for (uint256 k = 0; k < tokenIDs.length; k++) {
            //Closed NFTs are not considered
            if (ListedNFTs[tokenIDs[k]].nftState == NFT_STATE.CLOSED) {
                continue;
            }
            //Has NFT passed the interval?
            if ((block.timestamp - ListedNFTs[tokenIDs[k]].nftPostedTimeStamp) > nftInterval) {
                timePassed = true;
                break;
            }
        }
        upkeepNeeded = (isOpen && timePassed);
        return (upkeepNeeded, "0x0");
    }

    /**
     * @dev Once `checkUpkeep` is returning `true`, this function is called
     * and it kicks off a Chainlink VRF call to get a random winner.
     */
    function performUpkeep(bytes calldata /* performData */) external override {
        (bool upkeepNeeded, ) = checkUpkeep("");
        require(upkeepNeeded, "Upkeep not needed");

        //Before calling random number generator - clean up all NFTs and check if it has to be called
        bool hasToCallVRF = dailyNFTsCleanup();

        if (hasToCallVRF) {
            uint32 numWords =  uint32(currentClosingNFTs.length);

            uint256 requestId = i_vrfCoordinator.requestRandomWords(
                i_gasLane,
                i_subscriptionId,
                REQUEST_CONFIRMATIONS,
                i_callbackGasLimit,
                numWords
            );
            //Temporary: Call the fullfill directly
            //fulfillRandomWords(1, s_randomWords);
        }
    }

    function dailyNFTsCleanup() internal returns (bool) {
        bool hasToCallVRF = false;

        for (uint256 k = 0; k < tokenIDs.length; k++) {
            //Closed NFTs are not considered
            if (ListedNFTs[tokenIDs[k]].nftState == NFT_STATE.CLOSED) {
                continue;
            }
            //Step 1: Has NFT  passed the interval?
            if ((block.timestamp - ListedNFTs[tokenIDs[k]].nftPostedTimeStamp) > nftInterval) {
                //Step 2: NFT has passed the interval. There should be some offers. If so, time to call VRF. If not, close NFT.
                if (NFTOffers[tokenIDs[k]].length > 0) {
                    hasToCallVRF = true;
                    currentClosingNFTs.push(tokenIDs[k]); //NFTs that are slated to close today;
                } else {
                    //Close the NFT
                    ListedNFTs[tokenIDs[k]].nftState = NFT_STATE.CLOSED;
                    currentActiveNFTs--;
                    
                    //No buyer Mint to the hero
                    mint(tokenIDs[k], ListedNFTs[tokenIDs[k]].issuer, ListedNFTs[tokenIDs[k]].issuer, ListedNFTs[tokenIDs[k]].quantity);
                    emit NFTClosed(tokenIDs[k], ListedNFTs[tokenIDs[k]].quantity, 0);
                }
            }
        }
        return hasToCallVRF;
    }

    /**
     * @dev This is the function that Chainlink VRF node
     * calls to send the money to the random winner.
     */
    function fulfillRandomWords(uint256, /* requestId */
        uint256[] memory randomWords) internal override {
        //For each closing NFTs, first identify if # of offers are more than quantity.
        //If # of offers more than quantiy => use random to pick few
        //If # of offers are less than quantity => everyone is minted with NFT
        for (uint256 k = 0; k < currentClosingNFTs.length; k++) {
            //Close the NFT to start with
            ListedNFTs[currentClosingNFTs[k]].nftState = NFT_STATE.CLOSED;

            //# of offerers less than or equal to quantity => No random numeber
            if (NFTOffers[currentClosingNFTs[k]].length <= ListedNFTs[currentClosingNFTs[k]].quantity) {
                //Mint for everyone in the offer list for this token
                for (uint256 i = 0; i < NFTOffers[currentClosingNFTs[k]].length; i++) {
                    mint(currentClosingNFTs[k], NFTOffers[currentClosingNFTs[k]][i], ListedNFTs[currentClosingNFTs[k]].issuer, 1);
                }
                //No refund necessary -- but mint all remaining qty to hero
                mint(currentClosingNFTs[k], ListedNFTs[currentClosingNFTs[k]].issuer, ListedNFTs[currentClosingNFTs[k]].issuer, 
                    ListedNFTs[currentClosingNFTs[k]].quantity - NFTOffers[currentClosingNFTs[k]].length);

            } else {
                //Identify number of offerers and then use random generator to pick multiple offeres as per the quantity
                //expand the one VRF random numbers to total random number required to issue NFT based on quantity
                uint256[] memory expandedRandoms = expandRandomNumber(randomWords[k], ListedNFTs[currentClosingNFTs[k]].quantity);
                for (uint256 j = 0; j < ListedNFTs[currentClosingNFTs[k]].quantity; j++) {
                    //expan the random number
                    uint256 indexOfWinner = expandedRandoms[j] % NFTOffers[currentClosingNFTs[k]].length;

                    //call mint for the token and the for the winner - one token only;
                    mint(
                        currentClosingNFTs[k],
                        NFTOffers[currentClosingNFTs[k]][indexOfWinner],
                        ListedNFTs[currentClosingNFTs[k]].issuer, 1
                    );
                    OfferersOffered.push(NFTOffers[currentClosingNFTs[k]][indexOfWinner]);
                }
                //Refund Offerers who hasn't got the token
                for (uint256 i = 0; i < NFTOffers[currentClosingNFTs[k]].length; i++) {
                    //If this offerer is not in the offered list, then refund; decrese ethBalance
                    address offerer = NFTOffers[currentClosingNFTs[k]][i];
                    bool offererExistsForRefund = false;
                    for (uint256 m = 0; m < OfferersOffered.length; m++) {
                        if (OfferersOffered[m] == offerer) {
                            offererExistsForRefund =  true;
                        }
                    }
                    if (!offererExistsForRefund){
                       bool success = ethTransfer(currentClosingNFTs[k], NFTOffers[currentClosingNFTs[k]][i], ListedNFTs[currentClosingNFTs[k]].price);
                       if (success) {
                           ethBalance[currentClosingNFTs[k]] -=ListedNFTs[currentClosingNFTs[k]].price;
                       }
                    }
                }
            }
            
            //Cleanup OfferersOffered, decrement current active NFTs, emit event
            OfferersOffered = new address[](0);
            currentActiveNFTs--;
            emit NFTClosed(currentClosingNFTs[k], ListedNFTs[currentClosingNFTs[k]].quantity, NFTOffers[currentClosingNFTs[k]].length);
        }

        //reset the current closing NFT counter for next day;
        currentClosingNFTs = new uint256[](0);
    }

    function expandRandomNumber(uint256 randomValue, uint256 n) internal pure returns (uint256[] memory expandedValues) {
        expandedValues = new uint256[](n);
        for (uint256 i = 0; i < n; i++) {
            expandedValues[i] = uint256(keccak256(abi.encode(randomValue, i)));
        }
        return expandedValues;
    }

    function mint(uint256 _tokenId, address _offerer, address _issuer, uint256 _quantity) internal onlyOwner {
        //Mint the token to offerer - alwyas one quantity per address but unsold NFT's will be minted to heros
        
        //Update the contract with offer and quanity balance
        tokenBalance[_tokenId][_issuer]--;
        tokenBalance[_tokenId][_offerer] = 1;
        
        _mint(_offerer, _tokenId, _quantity, "");
        emit NFTMinted(_tokenId, _quantity, _offerer);
        emit NFTTransactions(_offerer, _tokenId, TRAN_TYPE.NFT_MINTED);

    }

    function withdraw(uint256 _tokenId) payable public {
        //Ony heros can call this function
        require(isValidHero(msg.sender) == true, "Invalid Hero");        
        //Ensuring issuer doesn't put themself on the offer
        require(ListedNFTs[_tokenId].issuer == msg.sender, "Invalid Hero token");
        //NFT is closed
        require(ListedNFTs[_tokenId].nftState == NFT_STATE.CLOSED,"NFT is still open");
        //There is a balance for this token still
        require(ethBalance[_tokenId] > 0, "Not enough fund");
        
        uint256 amount = ethBalance[_tokenId];
        ethBalance[_tokenId] = 0;

        bool success = ethTransfer(_tokenId, msg.sender, amount);
        require(success, "Transfer failed.");
        
        emit Withdraw(msg.sender, _tokenId, amount);
        emit NFTTransactions(msg.sender, _tokenId, TRAN_TYPE.WITHDWAR);
    }

    function ethTransfer(uint256 _tokenId, address _receiver, uint256 _ethAmt) internal returns(bool) {
        (bool success, ) = _receiver.call{value: _ethAmt}("");
        if (success) {
            emit ethTransferred(msg.sender, _tokenId, _ethAmt);
        }
        return success;
    }

    function uri(uint256 _tokenId) public view override returns (string memory){
        uint256 __token = _tokenId; 
        string memory _cid = ""; //TODO: fix CID - tokenURIs[_tokenId];
        return
            string(
                abi.encodePacked("https://gateway.pinata.cloud/ipfs/", _cid)
            );
    }

    function isValidToken(uint256 _tokenId) internal returns (bool) {
        for(uint256 i=0; i < tokenIDs.length; i++) {
            if (tokenIDs[i] == _tokenId) return true;
        }
        return false;
    }
    //Check if the Hero is valid -- Used to for adding tokens
    function isValidHero(address _hero) internal returns (bool) {
        return erstwhileHeros.heroExists(msg.sender);
    }

    //get count of all active NFTs
    function getTotalActiveNFTs() external view returns (uint256) {
        return currentActiveNFTs;
    }

    function getListedNFTs(uint256 _tokenId) external view returns(string memory tokenName, string memory tokenURI, 
        address issuer, uint256 quantity, uint256 price, uint256 nftPostedTimeStamp, NFT_STATE nftState){
        return (ListedNFTs[_tokenId].tokenName, ListedNFTs[_tokenId].tokenURI, ListedNFTs[_tokenId].issuer, 
            ListedNFTs[_tokenId].quantity, ListedNFTs[_tokenId].price, 
            ListedNFTs[_tokenId].nftPostedTimeStamp, ListedNFTs[_tokenId].nftState);
    }

    function getNFTOffererCount(uint256 _tokenId) external view returns(uint256){
        return NFTOffers[_tokenId].length;
    }

    function getEthBalance(address _balanceAddress) external view returns(uint256) {
        return _balanceAddress.balance;
    }

    function getEthBalanceOfContract() external view returns(uint256) {
        return address(this).balance;
    }

    function getEthBalanceOfToken(uint256 _tokenId) external view returns (uint256) {
        return ethBalance[_tokenId];
    }
    function getNFTBalance(uint256 _tokenId, address _balanceAddress) external view returns(uint256) {
        return tokenBalance[_tokenId][_balanceAddress];
    }
}
