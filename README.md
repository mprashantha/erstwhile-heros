> Note: This project is based on Chainlink-mix. To run the complete workflow in development, use the below command
 brownie run .\scripts\erstwhileHeros\deploy_test_erstwhileHeros_complete.py
 
 And for the rinkeby network --
 brownie run .\scripts\erstwhileHeros\deploy_test_erstwhileHeros_complete.py --netowkr rinkeby

 To do before you run the above script:
 1. Set 7 accounts and define the private key in .env file : ${PRIVATE_KEY1}
 2. Setup below two variables in .env file:
  export WEB3_INFURA_PROJECT_ID=
  export ETHERSCAN_TOKEN=

If you would like to manually trigger upkeep function, use below function (need to add your own contract address).
This is helpful during development
> brownie run .\scripts\erstwhileHeros\deploy_nft_dataSetup.py --network rinkeby

The project has mainly two smart contracts
1. ErstwhileHeors -- Defining the Heros
2. ErstwhileHerosNFT -- All transactional function of the program