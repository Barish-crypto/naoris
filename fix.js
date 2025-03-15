const fs = require('fs');

// Read the accounts.json file
const accountsData = JSON.parse(fs.readFileSync('accounts.json', 'utf8'));

// Update the accounts data to keep only the first deviceHash for each wallet
const updatedAccountsData = accountsData.map(account => ({
  walletAddress: account.walletAddress,
  deviceHash: parseInt(account.deviceHash[0], 10), // Keep only the first device hash as an integer
  token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ3YWxsZXRfYWRkcmVzcyI6IjB4YzQ3NWEzZjM2MmYyOTU2YzU3Y2EwZGQwZjI1ZjY2OTU2Y2VjYmM2MiIsImlkIjoiUFNnTUZVaE5vSVVnWnl5eSIsImlhdCI6MTczOTYyNDYxNywiZXhwIjoxNzQyMjE2NjE3fQ.v-QvZxRICtOz8mF7QsssZYCuk-ZE6n9G-ybGnHJ2sUE' // Add a token field
}));

// Write the updated data back to accounts.json
fs.writeFileSync('accounts.json', JSON.stringify(updatedAccountsData, null, 2));

console.log('accounts.json has been updated with only one device per wallet and a token field.');

