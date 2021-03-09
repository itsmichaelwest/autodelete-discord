# AutoDelete
A Discord bot that will delete messages in a channel after a period of time. This is a great way to create "ephemeral" channels where messages persist for a few minutes or hours.

There are no user-facing commands. Simply deploy the bot to the channels you want messages to be automatically deleted in, setting the correct timeouts, and the bot will do the rest. Ensure it has the *View Channel* and *Manage Messages* permissions to work properly.

This bot makes use of the [Discord.js](https://discord.js.org/) library.
## Developing
You'll need Node.

1. Clone the repository.
2. Run `yarn` to install dependencies.
3. Configure the bot using a `.env` file (or setting environment variables manually). See the section below.
4. Run `node index.js` to start the bot. It will log in to Discord with the API secret and present a ready message if all is good. It will now automatically remove messages from the channel after the time you specify.

## Configuring
To set up AutoDelete, you will want to set the following variables:

#### `TOKEN`
This is the bot's Discord token that you'll get from the Developer Portal. Simple!

#### `CHANNELS`
This is a comma-delimited string of channel IDs you want to the bot to operate in. You can get these IDs by enabling *Developer Mode* in the Discord app, right-clicking the channel and choosing *Copy ID*.

#### `TIMEOUTS`
This is also a comma-delimited string of numbers, representing time in minutes. Each timeout will be linked to the channel at the same position in the `CHANNELS` string (i.e. the first item in this string will be the timeout for the first channel).

If you need to use seconds instead of minutes, enter the value using the following calculation: `1 / 60 * [seconds] = value`.

## Known Issues

* This bot doesn't scale all that well. Trying to run it in many channels that are high volume could result in messages not being deleted on time.
* Discord API latency and limitations may result in messages being deleted a few seconds late. This is normal.
* By design the bot cannot access messages posted in a channel before it comes online, it only sees them at the time they are sent.

## Contributing
Bug fixes and improvements are always welcome, please feel free to make an issue or submit a pull request.