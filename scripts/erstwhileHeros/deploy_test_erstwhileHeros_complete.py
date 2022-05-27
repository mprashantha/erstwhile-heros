#!/usr/bin/python3
from brownie import (
    config,
    network,
    ErstwhileHeros,
    ErstwhileHerosNFT,
)
from web3 import Web3
import time
from scripts.helpful_scripts import (
    BLOCK_CONFIRMATIONS_FOR_VERIFICATION,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
    is_verifiable_contract,
)


def depoly_erstwhileHeros(account):
    # Print current network
    print(f"On network {network.show_active()}")

    # deploy #rstwhileHero
    erstwhileHeros = ErstwhileHeros.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    print(f"Contract deployed to {erstwhileHeros.address}")

    return erstwhileHeros

def add_hero(erstwhileHeros, heroAccount2, ownerAccount):
        # Mark the second account from brownie as Hero accont
    txAddHero = erstwhileHeros.addHeros(
        "Ashwath",
        "Great actor to remember",
        "https://image.org/ashwath.png",
        heroAccount1.address,
        {"from": ownerAccount},
    )
    txAddHero.wait(1)

    return 
def depoly_erstwhileHerosNFT(erstwhileHeros, account):
    # Get all the VRF details
    subscription_id = config["networks"][network.show_active()]["subscription_id"]
    gas_lane = config["networks"][network.show_active()]["gas_lane"]
    vrf_coordinator = get_contract("vrf_coordinator")

    # Deploy ErstwhileHerosNFT
    erstwhileHerosNFT = ErstwhileHerosNFT.deploy(
        erstwhileHeros,
        10,
        vrf_coordinator,
        subscription_id,
        gas_lane,
        100000,
        {"from": account},
    )

    print(f"Contract deployed to {erstwhileHerosNFT.address}")
    return erstwhileHerosNFT


def add_token(erstwhileHerosNFT, tokenID, heroAccount, quantity):
    tokenId = erstwhileHerosNFT.addToken(tokenID, "Test name", "http://token.uri/1", quantity, Web3.toWei(0.01, "ether"), "http://image.uri/1", {"from": heroAccount},)
    tokenId.wait(1)
    print(f"Token added with token {tokenID} with hero address {heroAccount} and total quantity {quantity}")


def main():
    print("###### --- START RUNNING THE DEPLOY & TEST ---- #######")
    ownerAccount = get_account(1)
    heroAccount1 = get_account(2)
    heroAccount2 = get_account(3)
    Offerer1 = get_account(4)
    Offerer2 = get_account(5)
    Offerer3 = get_account(6)
    Offerer4 = get_account(7)
    print(f"Owner accoount: {ownerAccount.address}")
    print(f"Hero accoount1: {heroAccount1.address}")
    print(f"Hero accoount2: {heroAccount2.address}")
    print(f"Offerer1 accoount: {Offerer1.address}")
    print(f"Offerer2 accoount: {Offerer2.address}")
    print(f"Offerer3 accoount: {Offerer3.address}")
    print(f"Offerer4 accoount: {Offerer4.address}")

    # Deploy ErstwhileHeros
    print("Deploying ErstwhileHeros")
    erstwhileHeros = depoly_erstwhileHeros(ownerAccount)


    # Confirm the added hero exists
    add_hero(erstwhileHeros, heroAccount1, ownerAccount)
    print(f"Hero 1 exists with address: {erstwhileHeros.heroExists(heroAccount1.address)}")

    # Mark the third account from brownie as Hero accont 2
    add_hero(erstwhileHeros, heroAccount2, ownerAccount)

    # Confirm the added hero exists
    print(f"Hero 2 exists with address: {erstwhileHeros.heroExists(heroAccount2.address)}")

    # Deploy ErstwhileHerosNFT
    erstwhileHerosNFT = depoly_erstwhileHerosNFT(erstwhileHeros, ownerAccount)
    print(f"Total Active NFTs after deployment of contract: {erstwhileHerosNFT.getTotalActiveNFTs()}")

    print(f"Current EthBalance Of Owner at the beginning: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 1 at the beginning: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of Hero 2 at the beginning: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of Offerer 1 at the beginning: {erstwhileHerosNFT.getEthBalance(Offerer1)}")
    print(f"Current EthBalance Of Offerer 2 at the beginning: {erstwhileHerosNFT.getEthBalance(Offerer2)}")

    ################## TOKEN 1 SETUP -> No offerers -> Perform should close the NFTs ##################
    print("################## TOKEN 1 SETUP -> No offerers -> Perform should close the NFTs ##################")
    # Add first token 1
    tokenID1 = 1
    add_token(erstwhileHerosNFT, tokenID1, heroAccount1, 2)
    print(f"Total Active NFTs after adding token 1: {erstwhileHerosNFT.getTotalActiveNFTs()}")

    # Retrieve token 1
    (tokenURI,tokenName,issuer,quantity,price,nftPostedTimeStamp,nftState,) = erstwhileHerosNFT.getListedNFTs(tokenID1)
    print(f"Token details for Token 1 after adding: Token ID: {tokenID1} {tokenName} Token URI: {tokenURI}, Token issuer: {issuer}, Token quantity: {quantity}, Token Price: {price}, Token Time: {nftPostedTimeStamp}, Token State: {nftState}")

    # Confirm if offerer is part of the list
    print(f"Offerer1 exists with token 1: {erstwhileHerosNFT.offererExists(tokenID1, Offerer1)}")
    print(f"Offerer2 exists with token 2: {erstwhileHerosNFT.offererExists(tokenID1, Offerer2)}")

    # -------------START PERFORM FOR TOKEN 1 -------------#
    print("#-------------START PERFORM FOR TOKEN 1 -------------#")
    # Pass 10 seconds to complete NFT interval
    time.sleep(10)

    print(f"Current EthBalance Of Owner before perform for toekn 1: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero after perform for token 1: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")

    try:
        # Call from Keepers
        txPerfom = erstwhileHerosNFT.performUpkeep("", {"from": ownerAccount})
        txPerfom.wait(1)
    except Exception as e:
        print("ERROR : " + str(e))

    print(f"Current EthBalance Of Owner after perform for token 1: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero after perform for token 1: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")

    # Retrieve token again for Token Id 1 to check the status - should be closed (which is 1)
    (
        tokenURI,
        tokenName,
        issuer,
        quantity,
        price,
        nftPostedTimeStamp,
        nftState,
    ) = erstwhileHerosNFT.getListedNFTs(tokenID1)
    print(f"Token details after perform for token 1 - Token ID: {tokenID1} Token URI: {tokenURI}, Token issuer: {issuer}, Token quantity: {quantity}, Token Price: {price}, Token Time: {nftPostedTimeStamp}, Token State: {nftState}")

    print(f"End of Token 1 perform - Total Active NFTs: {erstwhileHerosNFT.getTotalActiveNFTs()}")

    print("#-------------END PERFORM FOR TOKEN 1 -------------#")
    #### Nothing to withdraw for Token 1 ----- ####
    # -------------END PERFORM FOR TOKEN 1 -------------#

    ################## TOKEN 2 SETUP - 1 offerer -> 3 quantity -> perform should transfer token to offer (total qty > offerer)  ##################
    print("################## TOKEN 2 SETUP - 1 offerer -> 3 quantity -> perform should transfer token to offer  ##################")
    # Add a Token
    tokenID2 = 2
    add_token(erstwhileHerosNFT, tokenID2, heroAccount1, 3)
    print(f"Total Active NFTs after adding token 2: {erstwhileHerosNFT.getTotalActiveNFTs()}")

    # Retrieve token
    (
        tokenURI,
        tokenName,
        issuer,
        quantity,
        price,
        nftPostedTimeStamp,
        nftState,
    ) = erstwhileHerosNFT.getListedNFTs(tokenID2)
    print(f"Token details after adding token 2 - Token ID: {tokenID2} Token URI: {tokenURI}, Token issuer: {issuer}, Token quantity: {quantity}, Token Price: {price}, Token Time: {nftPostedTimeStamp}, Token State: {nftState}")

    # Add Offerer
    offerertx = erstwhileHerosNFT.addNFTOffer(tokenID2, {"from": Offerer1, "value": Web3.toWei(0.01, "ether")})
    offerertx.wait(1)
    print(f"Total NFTs offerer for token {tokenID2} is: {erstwhileHerosNFT.getNFTOffererCount(tokenID2)}")

    # Confirm if offerer is art of the list
    print(f"Offerer1 exists with token 2: {erstwhileHerosNFT.offererExists(tokenID2, Offerer1)}")
    print(f"Offerer2 exists with token 2: {erstwhileHerosNFT.offererExists(tokenID2, Offerer2)}")

    # -------------START PERFORM FOR TOKEN 2 -------------#
    print("#-------------START PERFORM FOR TOKEN 2 -------------#")
    # Pass 10 seconds to complete NFT interval
    time.sleep(10)

    print(f"Current EthBalance Of Owner before perform for toekn 2: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero before perform for token 2: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of Offerer 1 before perform for token 2: {erstwhileHerosNFT.getEthBalance(Offerer1)}")
    print(f"Current EthBalance Of token 2 before perform for token 2:{erstwhileHerosNFT.getEthBalanceOfToken(tokenID2)}")
    print(f"Current Token Balance Of token 2 for hero before perform for token 2:{erstwhileHerosNFT.getNFTBalance(tokenID2, heroAccount1)}")
    print(f"Current Token Balance Of token 2 for offerer 1 before perform for token 2:{erstwhileHerosNFT.getNFTBalance(tokenID2, Offerer1)}")

    try:
        # Call from Keepers
        txPerfom = erstwhileHerosNFT.performUpkeep("", {"from": ownerAccount})
        txPerfom.wait(1)
    except Exception as e:
        print("ERROR : " + str(e))

    print(f"Current EthBalance Of Owner after perform for toekn 2: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero after perform for token 2: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of Offerer 1 after perform for token 2: {erstwhileHerosNFT.getEthBalance(Offerer1)}")
    print(f"Current EthBalance Of token 2 after perform for token 2:{erstwhileHerosNFT.getEthBalanceOfToken(tokenID2)}")
    print(f"Current Token Balance Of token 2 for hero after perform for token 2:{erstwhileHerosNFT.getNFTBalance(tokenID2, heroAccount1)}")
    print(f"Current Token Balance Of token 2 for offerer 1 after perform for token 2:{erstwhileHerosNFT.getNFTBalance(tokenID2, Offerer1)}")

    # Retrieve token again for Token Id 2 to check the status - should be closed (1)
    (
        tokenURI,
        tokenName,
        issuer,
        quantity,
        price,
        nftPostedTimeStamp,
        nftState,
    ) = erstwhileHerosNFT.getListedNFTs(tokenID2)
    print(f"Token details after perform for token 2 - Token ID: {tokenID2} Token URI: {tokenURI}, Token issuer: {issuer}, Token quantity: {quantity}, Token Price: {price}, Token Time: {nftPostedTimeStamp}, Token State: {nftState}")

    print(f"End of Token 2 perform - Total Active NFTs: {erstwhileHerosNFT.getTotalActiveNFTs()}")

    print("#-------------END PERFORM FOR TOKEN 2 -------------#")
    # -------------END PERFORM FOR TOKEN 2 -------------#

    print("##### FINAL STEP -- Withdraw START for token 2 ------ ########")
    ##### FINAL STEP -- Withdraw START for token 2 ------ ########
    # Withdrawing for Hero 1 with token 2
    print(f"Current EthBalance Of Owner before withdraw: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 1 before withdraw: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of smart contract before withdraw: {erstwhileHerosNFT.getEthBalanceOfContract()}")
    print(f"Current EthBalance Of token 2 before withdraw: {erstwhileHerosNFT.getEthBalanceOfToken(tokenID2)}")
    txwithdraw = erstwhileHerosNFT.withdraw(tokenID2, {"from": heroAccount1})
    txwithdraw.wait(1)
    print(f"Current EthBalance Of Owner after widthdraw: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 2 after widthdraw: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of smart contract after withdraw: {erstwhileHerosNFT.getEthBalanceOfContract()}")
    print(f"Current EthBalance Of token 2 after withdraw: {erstwhileHerosNFT.getEthBalanceOfToken(tokenID2)}")
    ##### FINAL STEP -- Withdraw END for token 2 ------ ########
    print("##### FINAL STEP -- Withdraw END for token 2 ------ ########")
    print("##### END OF TOKEN 2")

    ################## TOKEN 3 SETUP - 4 offerer -> 2 quantity -> perform should transfer token to random offerers based on VRF #############
    print("################## TOKEN 3 SETUP - 4 offerer -> 2 quantity -> perform should transfer token to random offerers based on VRF #############")

    # Add a Token
    tokenID3 = 3
    add_token(erstwhileHerosNFT, tokenID3, heroAccount2, 2)

    # Retrieve token
    (
        tokenURI,
        tokenName,
        issuer,
        quantity,
        price,
        nftPostedTimeStamp,
        nftState,
    ) = erstwhileHerosNFT.getListedNFTs(tokenID3)
    print(f"Token details after adding token 3 - Token ID: {tokenID3} Token URI: {tokenURI}, Token issuer: {issuer}, Token quantity: {quantity}, Token Price: {price}, Token Time: {nftPostedTimeStamp}, Token State: {nftState}")

    # Add Offerer 1
    offerertx = erstwhileHerosNFT.addNFTOffer(
        tokenID3, {"from": Offerer1, "value": Web3.toWei(0.01, "ether")}
    )
    offerertx.wait(1)

    # Add Offerer 2
    offerertx = erstwhileHerosNFT.addNFTOffer(tokenID3, {"from": Offerer2, "value": Web3.toWei(0.01, "ether")})
    offerertx.wait(1)

    # Add Offerer 3
    offerertx = erstwhileHerosNFT.addNFTOffer(tokenID3, {"from": Offerer3, "value": Web3.toWei(0.01, "ether")})
    offerertx.wait(1)

    # Add Offerer 4
    offerertx = erstwhileHerosNFT.addNFTOffer(tokenID3, {"from": Offerer4, "value": Web3.toWei(0.01, "ether")})
    offerertx.wait(1)

    print(f"Total NFTs offerer for token 3 is: {erstwhileHerosNFT.getNFTOffererCount(tokenID3)}")

    # Confirm if offerer is part of the list
    print(f"Offerer1 exists with token 3: {erstwhileHerosNFT.offererExists(tokenID3, Offerer1)}")
    print(f"Offerer2 exists with token 3: {erstwhileHerosNFT.offererExists(tokenID3, Offerer2)}")
    print(f"Offerer3 exists with token 3: {erstwhileHerosNFT.offererExists(tokenID3, Offerer3)}")
    print(f"Offerer4 exists with token 3: {erstwhileHerosNFT.offererExists(tokenID3, Offerer4)}")

    # -------------START PERFORM FOR TOKEN 3 -------------#
    print("#-------------START PERFORM FOR TOKEN 3 -------------#")
    # Pass 10 seconds to complete NFT interval
    time.sleep(10)

    print(f"Current EthBalance Of Owner before perform for toekn 3: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 2 before perform for token 3: {erstwhileHerosNFT.getEthBalance(heroAccount2)}")
    print(f"Current EthBalance Of Offerer 1 before perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer1)}")
    print(f"Current EthBalance Of Offerer 2 before perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer2)}")
    print(f"Current EthBalance Of Offerer 3 before perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer3)}")
    print(f"Current EthBalance Of Offerer 4 before perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer4)}")
    print(f"Current EthBalance Of token 3 before perform for token 3:{erstwhileHerosNFT.getEthBalanceOfToken(tokenID3)}")
    print(f"Current Token Balance Of token 3 for hero 2 before perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, heroAccount2)}")
    print(f"Current Token Balance Of token 3 for offerer 1 before perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer1)}")
    print(f"Current Token Balance Of token 3 for offerer 2 before perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer2)}")
    print(f"Current Token Balance Of token 3 for offerer 3 before perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer3)}")
    print(f"Current Token Balance Of token 3 for offerer 4 before perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer4)}")

    try:
        # Call from Keepers
        txPerfom = erstwhileHerosNFT.performUpkeep("", {"from": ownerAccount})
        txPerfom.wait(1)
    except Exception as e:
        print("ERROR : " + str(e))

    print(f"Current EthBalance Of Owner after perform for toekn 3: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 2 after perform for token 3: {erstwhileHerosNFT.getEthBalance(heroAccount2)}")
    print(f"Current EthBalance Of Offerer 1 after perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer1)}")
    print(f"Current EthBalance Of Offerer 2 after perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer2)}")
    print(f"Current EthBalance Of Offerer 3 after perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer3)}")
    print(f"Current EthBalance Of Offerer 4 after perform for token 3: {erstwhileHerosNFT.getEthBalance(Offerer4)}")
    print(f"Current EthBalance Of token 3 after perform for token 3:{erstwhileHerosNFT.getEthBalanceOfToken(tokenID3)}")
    print(f"Current Token Balance Of token 3 for hero 2 after perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, heroAccount2)}")
    print(f"Current Token Balance Of token 3 for offerer 1 after perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer1)}")
    print(f"Current Token Balance Of token 3 for offerer 2 after perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer2)}")
    print(f"Current Token Balance Of token 3 for offerer 3 after perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer3)}")
    print(f"Current Token Balance Of token 3 for offerer 4 after perform for token 3:{erstwhileHerosNFT.getNFTBalance(tokenID3, Offerer4)}")

    # Retrieve token again for Token Id 2 to check the status - should be closed (1)
    (
        tokenURI,
        tokenName,
        issuer,
        quantity,
        price,
        nftPostedTimeStamp,
        nftState,
    ) = erstwhileHerosNFT.getListedNFTs(tokenID3)
    print(f"Token details after perform for token 3 - Token ID: {tokenID3} Token URI: {tokenURI}, Token issuer: {issuer}, Token quantity: {quantity}, Token Price: {price}, Token Time: {nftPostedTimeStamp}, Token State: {nftState}")

    print(f"End of Token 3 perform - Total Active NFTs: {erstwhileHerosNFT.getTotalActiveNFTs()}")

    print("#-------------END PERFORM FOR TOKEN 3 -------------#")
    # -------------END PERFORM FOR TOKEN 3 -------------#

    ##### FINAL STEP -- Withdraw -- START TOKEN 3------ ########
    print("##### FINAL STEP -- Withdraw -- START TOKEN 3------ ########")
    # Withdrawing for Hero 2 with token 3
    print(f"Current EthBalance Of Owner before withdraw: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 2 before withdraw: {erstwhileHerosNFT.getEthBalance(heroAccount2)}")
    print(f"Current EthBalance Of smart contract before withdraw: {erstwhileHerosNFT.getEthBalanceOfContract()}")
    print(f"Current EthBalance Of token 3 before withdraw: {erstwhileHerosNFT.getEthBalanceOfToken(tokenID3)}")
    txwithdraw = erstwhileHerosNFT.withdraw(tokenID3, {"from": heroAccount2})
    txwithdraw.wait(1)
    print(f"Current EthBalance Of Owner after widthdraw: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 2 after widthdraw: {erstwhileHerosNFT.getEthBalance(heroAccount2)}")
    print(f"Current EthBalance Of smart contract after withdraw: {erstwhileHerosNFT.getEthBalanceOfContract()}")
    print(f"Current EthBalance Of token 3 after withdraw: {erstwhileHerosNFT.getEthBalanceOfToken(tokenID3)}")
    print("##### FINAL STEP -- Withdraw -- END ------ ########")
    ##### FINAL STEP -- Withdraw -- END ------ ########

    print("##### END OF TOKEN 3")

    print("-----DONE WITH THE SCRIPT-----")


def submain():
    vrf_consumer = depoly_vrf_consumer()
    vrf_consumer = VRFConsumerV2[-1]
    account = get_account()
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        add_vrf_consumer_to_subscription(
            config["networks"][network.show_active()]["subscription_id"], vrf_consumer
        )
    try:
        tx = vrf_consumer.requestRandomWords({"from": account})
        tx.wait(1)
    except:
        print(    "Remember to fund your subscription! \n You can do it with the scripts here, or at https://vrf.chain.link/"
        )
    print("Random number Requested!")

    try:
        time.sleep(5)
        print(f"Random word 0 is {vrf_consumer.s_randomWords(0)}")
        print(f"Random word 1 is {vrf_consumer.s_randomWords(1)}")
    except:
        print("You may have to wait a minute unless on a local chain!")


def add_vrf_consumer_to_subscription(subscription_id, vrf_consumer):
    vrf_coordinator = get_contract("vrf_coordinator")
    subscription_details = vrf_coordinator.getSubscription(subscription_id)
    if vrf_consumer in subscription_details[3]:
        print(f"{vrf_consumer} is already in the subscription")
    else:
        print(    f"Adding consumer to subscription {subscription_id} on address {vrf_consumer}"
        )
        account = get_account()
        tx = vrf_coordinator.addConsumer.transact(
            subscription_id, vrf_consumer.address, {"from": account}
        )
        tx.wait(1)
        print("Consumer added to subscription!")