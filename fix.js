const fs = require('fs');

// Read the accounts.json file
const accountsData = JSON.parse(fs.readFileSync('accounts.json', 'utf8'));

// Update the accounts data to keep only the first deviceHash for each wallet
const updatedAccountsData = accountsData.map(account => ({
  walletAddress: account.walletAddress,
  deviceHash: account.deviceHash.slice(0, 1) // Keep only the first device hash
}));

// Write the updated data back to accounts.json
fs.writeFileSync('accounts.json', JSON.stringify(updatedAccountsData, null, 2));

console.log('accounts.json has been updated with only one device per wallet.');

