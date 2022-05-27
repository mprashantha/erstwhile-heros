#!/usr/bin/python3
from brownie import (
    config,
    network,
    Contract,
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

def load_from_contract_address_erstwhileHerosNFT():
    erstwhileHerosNFT = Contract.from_abi(ErstwhileHerosNFT._name, "0x9D1cFe2ec3f50E3E59Ee71426fbBBf4724Fd2f42", ErstwhileHerosNFT.abi)
    heroAccount = get_account(3)
    print(erstwhileHerosNFT.address)

    #add token
    tx = erstwhileHerosNFT.addToken(
        4,
        "http://token.uri/4",
        3,
        Web3.toWei(0.01, "ether"), "http://image.uri/4",
        {"from": heroAccount},
    )
    tx.wait(1)
    print(f"Token added with token 4 with hero address {heroAccount} and total quantity 3")


def depoly_erstwhileHeros(account):
    # Print current network
    print(f"On network {network.show_active()}")

    # deploy #rstwhileHero
    erstwhileHeros = ErstwhileHeros.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    print(f"Contract deployed to {erstwhileHeros}")

    return erstwhileHeros


def depoly_erstwhileHerosNFT(erstwhileHeros, account):
    # Get all the VRF details
    subscription_id = config["networks"][network.show_active()]["subscription_id"]
    gas_lane = config["networks"][network.show_active()]["gas_lane"]
    vrf_coordinator = get_contract("vrf_coordinator")

    # Deploy ErstwhileHerosNFT
    erstwhileHerosNFT = ErstwhileHerosNFT.deploy(
        erstwhileHeros,
        600,
        vrf_coordinator,
        subscription_id,
        gas_lane,
        100000,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )

    print(f"Contract deployed to {erstwhileHerosNFT}")
    return erstwhileHerosNFT

def deploy_hero_nft_contracts():
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

    # Deploy ErstwhileHerosNFT
    erstwhileHerosNFT = depoly_erstwhileHerosNFT(erstwhileHeros, ownerAccount)
    print(f"Total Active NFTs after deployment of contract: {erstwhileHerosNFT.getTotalActiveNFTs()}")

    print(f"Current EthBalance Of Owner at the beginning: {erstwhileHerosNFT.getEthBalance(ownerAccount)}")
    print(f"Current EthBalance Of Hero 1 at the beginning: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of Hero 2 at the beginning: {erstwhileHerosNFT.getEthBalance(heroAccount1)}")
    print(f"Current EthBalance Of Offerer 1 at the beginning: {erstwhileHerosNFT.getEthBalance(Offerer1)}")
    print(f"Current EthBalance Of Offerer 2 at the beginning: {erstwhileHerosNFT.getEthBalance(Offerer2)}")


def load_from_contract_address_erstwhileHerosNFT_perform():
    erstwhileHerosNFT = Contract.from_abi(ErstwhileHerosNFT._name, "0x5e489166Bc125E487E0AB74F539D1C4EbeDF52Aa", ErstwhileHerosNFT.abi)
    print(erstwhileHerosNFT)
    tx = erstwhileHerosNFT.performUpkeep("", {"from":get_account(1), 'gas_limit': 5500000})
    tx.wait(1)
    print(f"perform called")

def main():
    #load_from_contract_address_erstwhileHerosNFT()
    load_from_contract_address_erstwhileHerosNFT_perform()
