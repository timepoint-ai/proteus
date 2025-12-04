require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Helper function to get accounts for deployment
function getDeployerAccounts() {
  const pk = process.env.DEPLOYER_PRIVATE_KEY;
  if (!pk || pk.length < 64) {
    return [];
  }
  return [pk.startsWith('0x') ? pk : `0x${pk}`];
}

// Helper function to get test accounts
function getTestAccounts() {
  const testPk = process.env.TEST_WALLET_PRIVATE_KEY;
  const deployPk = process.env.DEPLOYER_PRIVATE_KEY;

  const accounts = [];

  // Add test wallet if available
  if (testPk && testPk.length >= 64) {
    accounts.push(testPk.startsWith('0x') ? testPk : `0x${testPk}`);
  }

  // Add deployer if different from test wallet
  if (deployPk && deployPk.length >= 64) {
    const formatted = deployPk.startsWith('0x') ? deployPk : `0x${deployPk}`;
    if (!accounts.includes(formatted)) {
      accounts.push(formatted);
    }
  }

  return accounts;
}

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      },
      viaIR: true
    }
  },
  networks: {
    // Local development - uses Hardhat's built-in accounts (funded automatically)
    hardhat: {
      chainId: 31337,
      // Fork BASE Sepolia for realistic testing (optional)
      // forking: {
      //   url: process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org",
      //   enabled: false
      // }
    },
    // Localhost - for running hardhat node separately
    localhost: {
      url: process.env.HARDHAT_NETWORK_URL || "http://127.0.0.1:8545",
      chainId: 31337
    },
    // BASE Sepolia Testnet - uses test wallet
    baseSepolia: {
      url: process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org",
      accounts: getTestAccounts(),
      chainId: 84532,
      gasPrice: 1000000000, // 1 gwei
    },
    // BASE Mainnet - uses deployer wallet (production)
    base: {
      url: process.env.BASE_RPC_URL || "https://mainnet.base.org",
      accounts: getDeployerAccounts(),
      chainId: 8453
    }
  },
  etherscan: {
    apiKey: {
      baseSepolia: process.env.BASESCAN_API_KEY || "",
      base: process.env.BASESCAN_API_KEY || ""
    },
    customChains: [
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api-sepolia.basescan.org/api",
          browserURL: "https://sepolia.basescan.org"
        }
      },
      {
        network: "base",
        chainId: 8453,
        urls: {
          apiURL: "https://api.basescan.org/api",
          browserURL: "https://basescan.org"
        }
      }
    ]
  },
  paths: {
    sources: "./contracts/src",
    tests: "./contracts/test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};