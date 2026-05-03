import { ClobClient, OrderType, Side } from '@polymarket/clob-client';
import { createWalletClient, http } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { polygon } from 'viem/chains';

const HOST = 'https://clob.polymarket.com';
const CHAIN_ID = 137;
const tokenId = process.argv[2];
const price = parseFloat(process.argv[3]);
const usdSize = parseFloat(process.argv[4]);

if (!tokenId || !price || !usdSize) {
  console.error('Usage: node place_order.mjs <token_id> <price> <usd_size>');
  process.exit(1);
}
const pk = process.env.PRIVATE_KEY;
if (!pk) { console.error('PRIVATE_KEY env required'); process.exit(1); }

const account = privateKeyToAccount(pk);
const wallet = createWalletClient({ account, chain: polygon, transport: http() });
console.log(`signer: ${account.address}`);

// Step 1: bootstrap client without creds, derive
const bootstrap = new ClobClient(HOST, CHAIN_ID, wallet, undefined, 0, account.address);
console.log('deriving api creds...');
const creds = await bootstrap.createOrDeriveApiKey();
console.log(`api_key: ${creds.key.slice(0,8)}...`);

// Step 2: construct full client WITH creds
const client = new ClobClient(HOST, CHAIN_ID, wallet, creds, 0, account.address);

const sizeShares = +(usdSize / price).toFixed(4);
console.log(`placing limit BUY ${sizeShares} shares @ $${price} of token ${tokenId.slice(0,12)}...`);

try {
  const order = await client.createOrder({
    tokenID: tokenId, price, side: Side.BUY, size: sizeShares, feeRateBps: 0,
  });
  console.log(`signed order created`);
  const result = await client.postOrder(order, OrderType.GTC);
  console.log(`POST result: ${JSON.stringify(result, null, 2)}`);
} catch (e) {
  console.error(`FAILED: ${e.message}`);
  if (e.response?.data) console.error(`  body: ${JSON.stringify(e.response.data)}`);
  process.exit(2);
}
