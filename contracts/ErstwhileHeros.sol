// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/access/Ownable.sol";

/** @title ErstwhileHeros
 *   @notice Contract to manage all transaction related to NFT Market place
 *   @author Prashantha M
 */
contract ErstwhileHeros is Ownable {
    // ErstwhileHeros Variables
    struct HeorsInfo {
        string name;
        string profile;
        string imgUrl;
        address heroAddress;
    }

    //events
    event HerosCreated(string name, string profile, string imgUrl, address heroAddress);

    mapping(address => HeorsInfo) Heros; //All Heros

    function addHeros(string memory _name, string memory _profile, string memory _imgUrl, address _heroAddress) external onlyOwner {
        require(!heroExists(_heroAddress), "Hero already exists");

        Heros[_heroAddress] = HeorsInfo(_name, _profile, _imgUrl, _heroAddress);

        emit HerosCreated(_name, _profile, _imgUrl, _heroAddress);
    }

    function heroExists(address _address) public view returns (bool) {
        return Heros[_address].heroAddress != address(0);
    }
}