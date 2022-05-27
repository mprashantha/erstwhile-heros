import time
import pytest
from brownie import VRFConsumerV2, ErstwhileHerosNFT, ErstwhileHeros, convert, network, config
from scripts.helpful_scripts import (
    get_account,
    get_contract,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    listen_for_event,
)

from scripts.vrf_scripts.create_subscription import (
    create_subscription,
    fund_subscription,
)

from scripts.erstwhileHeros.deploy_test_erstwhileHeros_complete import (
    depoly_erstwhileHeros,
    depoly_erstwhileHerosNFT,
    add_token,
    add_hero,
)

def test_end_to_end_workflow():
    print("###### --- START RUNNING THE DEPLOY & TEST ---- #######")
    ownerAccount = get_account(1)
    heroAccount1 = get_account(2)
    heroAccount2 = get_account(3)
    Offerer1 = get_account(4)
    Offerer2 = get_account(5)
    Offerer3 = get_account(6)
    Offerer4 = get_account(7)

    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    
    #Hero work flow
    # Arrange
    erstwhileHeros = depoly_erstwhileHeros(ownerAccount)

    # Act
    add_hero(erstwhileHeros, heroAccount1, ownerAccount)

    # Assert
    assert {erstwhileHeros.heroExists(heroAccount1.address)}

    #Token workflow
    # Arrange
    erstwhileHerosNFT = depoly_erstwhileHerosNFT(erstwhileHeros, ownerAccount)

    #Act
    add_token(erstwhileHerosNFT, 1, heroAccount1, 2)
    
    #Assert
    (tokenURI,tokenName,issuer,quantity,price,nftPostedTimeStamp,nftState,) = erstwhileHerosNFT.getListedNFTs(1)
    assert {issuer.address == heroAccount1.address}

    #Perform workflow without Offerer
    #Arrange
    #None -- NFT has been already there

    #Act
    try:
        # Call from Keepers
        txPerfom = erstwhileHerosNFT.performUpkeep("", {"from": ownerAccount})
        txPerfom.wait(1)
    except Exception as e:
        print("ERROR : " + str(e))

    #Assert
    (
        tokenURI,
        tokenName,
        issuer,
        quantity,
        price,
        nftPostedTimeStamp,
        nftState,
    ) = erstwhileHerosNFT.getListedNFTs(1)
    assert (nftState == 1) #NFT should be closed by now