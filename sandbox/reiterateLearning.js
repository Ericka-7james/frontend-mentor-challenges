const transactions = [ 
    { id : 1, name: "ALice", amount: 50, category: "groceries" },
    {id : 2, name: "Bob", amount: 40, category: "entertainment" },
    {id: 3, name: "Jessica", amount: 70, category: "Travel"},
    {id: 4, name: "Michael", amount: 30, category: "Bills"},
    {id: 5, name: "Sarah", amount: 90, category: "SaaS"},
]

console.log(transactions);

const categoryBills = transactions.filter(transactions => transactions.category === "Bills");
console.log("Bills:", categoryBills);

const bigTransactions = transactions.filter(transactions => transactions.amount > 50);
console.log("Big Transactions:", bigTransactions);

const transactionNames = transactions.map(transactions => transactions.name);
console.log("Transaction Names:", transactionNames);4

const formmattedTransactions2 = transactions.map(transactions => {
    return ` ${transactions.name} spent $${transactions.amount} on ${transactions.category} `;
});
console.log("Formatted Transactions 2:", formmattedTransactions2);

const amounts = transactions.map(transactions => transactions.amount);
console.log("Amounts:", amounts);

const sortedLowToHigh = transactions.sort((a, b) => a.amount - b.amount);
console.log("Sorted Low to High:", sortedLowToHigh);

const sortedHighToLow = transactions.sort((a,b) => b.amount - a.amount);
console.log("Sorted High to Low:", sortedHighToLow);

const sortedAlphabetically = transactions.sort((a,b) => {
    if (a.name < b.name) {
        return -1;
    }
    if (a.name > b.name) {
        return 1;
    }
    return 0;
});
console.log("Sorted Alphabetically:", sortedAlphabetically);

const sortedAlphabetically2 = transactionNames.sort((a,b) => a.name - b.name);
console.log("Sorted Alphabetically 2:", sortedAlphabetically2);