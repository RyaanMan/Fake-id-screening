import fs from "node:fs";
import path from "node:path";
import solc from "solc";
import { JsonRpcProvider, Wallet, ContractFactory } from "ethers";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const sourcePath = path.join(root, "contracts", "DocumentRegistry.sol");
const source = fs.readFileSync(sourcePath, "utf8");

const input = {
  language: "Solidity",
  sources: {
    "DocumentRegistry.sol": { content: source }
  },
  settings: {
    optimizer: { enabled: true, runs: 200 },
    outputSelection: {
      "*": { "*": ["abi", "evm.bytecode"] }
    }
  }
};

const output = JSON.parse(solc.compile(JSON.stringify(input)));
if (output.errors) {
  const errors = output.errors.filter((e) => e.severity === "error");
  if (errors.length) {
    console.error(errors.map((e) => e.formattedMessage).join("\n"));
    process.exit(1);
  }
}

const artifact = output.contracts["DocumentRegistry.sol"]["DocumentRegistry"];
const rpcUrl = process.env.BLOCKCHAIN_RPC_URL || "http://127.0.0.1:8545";
const privateKey = process.env.BLOCKCHAIN_PRIVATE_KEY;

if (!privateKey) {
  console.error("Set BLOCKCHAIN_PRIVATE_KEY to one of the private keys printed by `npm run node`.");
  process.exit(1);
}

const provider = new JsonRpcProvider(rpcUrl);
const wallet = new Wallet(privateKey, provider);
const factory = new ContractFactory(artifact.abi, artifact.evm.bytecode.object, wallet);
const contract = await factory.deploy();
await contract.waitForDeployment();
const address = await contract.getAddress();

const deployment = { address, abi: artifact.abi, deployer: wallet.address };
fs.writeFileSync(path.join(root, "deployment.json"), JSON.stringify(deployment, null, 2));

console.log(`Deployed DocumentRegistry: ${address}`);
console.log(`Deployer: ${wallet.address}`);
console.log("Wrote blockchain/deployment.json");
