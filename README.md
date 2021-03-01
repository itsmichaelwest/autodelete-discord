# AutoDelete
A Discord bot that will delete messages in a channel after a period of time.

This bot makes use of the [Discord.js](https://discord.js.org/) library.

## Developing
You'll need Node.

1. Clone the repository.
2. Run `yarn` to install dependencies.
3. Create a `.env` file and populate it with the following :
    * `TOKEN`: Your Discord bot token
    * `CHANNEL`: The channel you want to the bot to work on. You can get this by enabling developer mode in Discord, right-clicking the channel and choosing *Copy ID*.
    * `TIMEOUT_MINUTES`: The number of minutes to delete the message after.
4. Run `node index.js` to start the bot. It will log in to Discord with the API secret and present a ready message if all is good. It will now automatically remove messages from the channel after the time you specify.

## Contributing
Bug fixes and improvements are always welcome, please feel free to make an issue or submit a pull request.