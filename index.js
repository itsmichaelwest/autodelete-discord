const Discord = require('discord.js');
const client = new Discord.Client();
if (process.env.NODE_ENV !== 'production') {
    require('dotenv').config();
}

const channels = process.env.CHANNELS.split(',')
const timeouts = process.env.TIMEOUTS.split(',')
let timeoutMilliseconds = []

client.login(process.env.TOKEN);

// Login, convert the timeouts to milliseconds and print information to console.
client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
    timeouts.forEach(timeout => { timeoutMilliseconds.push(timeout * 60000) })
    for (const index in channels) {
        console.log(`Operating in channel ID: ${channels[index]} with a timeout of ${timeoutMilliseconds[index]} milliseconds (that's ${timeouts[index]} minute(s))`)
    }
});

client.on('message', async message => {
    // We can't use foreach here, we need the index to line up with the timeouts.
    for (const index in channels) {
        console.log(channels[index])
        if (message.channel.id === channels[index]) {
            setTimeout(() => message.delete(), timeoutMilliseconds[index]);
        }
    }
});

// Spin up a basic HTML front-end page.
const http = require('http');
const server = http.createServer((request, response) => {
    response.writeHead(200, {"Content-Type": "text/plain"});
    response.end(`Hi, I'm AutoDelete!`);
});
const port = process.env.PORT || 1337;
server.listen(port);