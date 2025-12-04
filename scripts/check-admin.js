const { ethers } = require("hardhat");

async function main() {
  const provider = new ethers.JsonRpcProvider("https://sepolia.base.org");
  
  // Contract addresses
  const actorRegistryAddr = "0xC71CC19C5573C5E1E144829800cD0005D0eDB723";
  const nodeRegistryAddr = "0xA69C842F335dfE1F69288a70054A34018282218d";
  
  // ActorRegistry ABI for admin checks
  const actorABI = [
    "function hasRole(bytes32 role, address account) view returns (bool)",
    "function DEFAULT_ADMIN_ROLE() view returns (bytes32)",
    "function ADMIN_ROLE() view returns (bytes32)",
    "function nodeRegistry() view returns (address)"
  ];
  
  // NodeRegistry ABI
  const nodeABI = [
    "function owner() view returns (address)",
    "function MINIMUM_STAKE() view returns (uint256)",
    "function activeNodeCount() view returns (uint256)"
  ];
  
  const actorRegistry = new ethers.Contract(actorRegistryAddr, actorABI, provider);
  const nodeRegistry = new ethers.Contract(nodeRegistryAddr, nodeABI, provider);
  
  // Check NodeRegistry owner and settings
  console.log("=== NodeRegistry ===");
  const nodeOwner = await nodeRegistry.owner();
  console.log("Owner:", nodeOwner);
  const minStake = await nodeRegistry.MINIMUM_STAKE();
  console.log("Minimum Stake:", ethers.formatEther(minStake), "ETH");
  const activeNodes = await nodeRegistry.activeNodeCount();
  console.log("Active Nodes:", activeNodes.toString());
  
  // Check ActorRegistry admin
  console.log("\n=== ActorRegistry ===");
  const defaultAdminRole = await actorRegistry.DEFAULT_ADMIN_ROLE();
  const adminRole = await actorRegistry.ADMIN_ROLE();
  console.log("DEFAULT_ADMIN_ROLE:", defaultAdminRole);
  console.log("ADMIN_ROLE:", adminRole);
  
  // Check if test wallet has admin role
  const testWallet = "0x21a85AD98641827BFd89F4d5bC2fEB72F98aaecA";
  const isTestAdmin = await actorRegistry.hasRole(defaultAdminRole, testWallet);
  console.log("Test wallet has DEFAULT_ADMIN_ROLE:", isTestAdmin);
  
  // Check if node owner has admin role
  const isOwnerAdmin = await actorRegistry.hasRole(defaultAdminRole, nodeOwner);
  console.log("NodeRegistry owner has DEFAULT_ADMIN_ROLE:", isOwnerAdmin);
}

main().catch(console.error);
