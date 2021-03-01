const Discord = require('discord.js');
const client = new Discord.Client();
if (process.env.NODE_ENV !== 'production') {
    require('dotenv').config();
}

const timeMinutes = process.env.TIMEOUT_MINUTES;
const timeout = (timeMinutes * (60000));

client.login(process.env.TOKEN);

client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
    console.log(`Messages will timeout after ${timeout} milliseconds (that's ${timeMinutes} minute(s))`);
    client.user.setActivity('with a recycle bin', { type: 'PLAYING' });
});

client.on('message', async message => {
    if (message.channel.id === process.env.CHANNEL) {
        setTimeout(() => message.delete(), timeout);
    }
});

// Spin up a basic HTTP front-end so Azure doesn't put us to sleep.
const http = require('http');
const server = http.createServer((request, response) => {
    response.writeHead(200, {"Content-Type": "text/plain"});
    response.end(`Hi, I'm ${name}! This page serves to keep the bot process up 24/7 on Microsoft Azure.`);
});
const port = process.env.PORT || 1337;
server.listen(port);