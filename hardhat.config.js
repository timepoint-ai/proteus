require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Helper function to get accounts
function getAccounts() {
  const pk = process.env.DEPLOYER_PRIVATE_KEY;
  if (!pk || pk.length < 64) {
    // Return empty array if no valid private key
    return [];
  }
  // Ensure proper formatting
  return [pk.startsWith('0x') ? pk : `0x${pk}`];
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
    hardhat: {
      chainId: 31337
    },
    baseSepolia: {
      url: process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org",
      accounts: getAccounts(),
      chainId: 84532
    },
    base: {
      url: process.env.BASE_RPC_URL || "https://mainnet.base.org",
      accounts: getAccounts(),
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