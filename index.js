import Discord from 'discord.js'
const client = new Discord.Client({ partials: ['MESSAGE', 'CHANNEL', 'REACTION'] })
import { Low, JSONFile } from 'lowdb'
import { fileURLToPath } from 'url'
const prefix = '!'

import dotenv from 'dotenv'
dotenv.config({ silent: process.env.NODE_ENV === 'production' })

const dbFile2 = fileURLToPath(new URL('db.json', import.meta.url))
const dbAdapter = new JSONFile(dbFile2)
const db = new Low(dbAdapter)

// Login to Discord API
client.login(process.env.TOKEN)

// Convert the timeouts to milliseconds and print information to console.
client.on('ready', async () => {
    // Read database file
    await db.read()
    if (!db.data) {
        db.data = {
            settings: {
                channels: [],
                timeouts: [],
                archive: ''
            } 
        }
    }
    // Write database if it doesn't exist
    await db.write()

    console.log(`Logged in as ${client.user.tag}!`);
});

// When message is received, set a timeout to delete it.
client.on('message', async message => {
    if (!message.content.startsWith(prefix)) {
        // We can't use foreach here, we need the index to line up with the timeouts.
        for (const index in db.data.settings.channels) {
            if (message.channel.id === db.data.settings.channels[index]) {
                setTimeout(() => message.delete(), db.data.settings.timeouts[index])
                break
            }
        }
    } else {
        const args = message.content.slice(prefix.length).trim().split(/ +/)
        const command = args.shift().toLowerCase()
    
        // Admin commands
        switch (command) {
            case 'adx':
                if (message.member.hasPermission(Discord.Permissions.FLAGS.ADMINISTRATOR)) {
                    switch (args[0]) {
                        case 'channel':
                            switch (args[1]) {
                                case 'add':
                                    db.data.settings.channels.push(args[2])
                                    db.data.settings.timeouts.push(args[3] * 60000)
                                    await db.write()
                                    break
                                case 'remove':
                                    const index = db.data.settings.channels.indexOf(args[2])
                                    if (index > -1) {
                                        db.data.settings.channels.splice(index, 1)
                                        db.data.settings.timeouts.splice(index, 1)
                                    }
                                    await db.write()
                                    break
                            }
                            break
                        case 'archive':
                            switch (args[1]) {
                                case 'set':
                                    db.data.settings.archive = args[2]
                                    await db.write()
                                    break
                                case 'clear':
                                    db.data.settings.archive = ""
                                    await db.write()
                                    break
                            }
                            break
                        case 'clear':
                            message.channel.send(`**Clearing <#${message.channel.id}>.** This may take some time, depending on the number of messages to delete due to Discord API restrictions.`)
                            let fetched
                            do {
                                fetched = await message.channel.messages.fetch({limit: 100})
                                console.log(`Fetched size is ${fetched.size}`)
                                await message.channel.bulkDelete(fetched)
                                console.log('Deleted 100 messages')
                            } while(fetched.size >= 2)
                            console.log('Done!')
                            break
                        case 'help':
                            message.channel.send(
                                `**AutoDelete administration reference**\n\`channel [add|remove] [channel ID] [timeout minutes]\` - Add or remove a channel from the automatic deletion list. The timeout value is required when adding a new channel.\n\`archive [set|clear] [channel ID]\` - Set or clear the channel used for archiving messages. If the channel is cleared, users will not be able to archive their messages.\n\`clear\` - Clears the current channel of all messages.`
                            )
                            break
                        case 'fetch':
                            message.channel.messages.fetch({ limit: 1 }).then(msg => {
                                msg.forEach(m => {
                                    if (m.reference) {
                                        message.channel.messages.fetch(m.reference.messageID).then(m2 => {
                                            message.channel.send('```json\n' + JSON.stringify(m2, null, '\t') + '\n```')
                                        })
                                    }
                                })
                            })
                            break
                        case 'forcearchive':
                            if (db.data.settings.channels.includes(message.channel.id)) {
                                message.channel.messages.fetch(args[1]).then(async msg => {
                                    if (!msg.partial) {
                                        const embed = new Discord.MessageEmbed()
                                            .setAuthor(msg.member.displayName, msg.author.displayAvatarURL())
                                            .setDescription(msg.content)
                                            .setFooter(`Archived by ${msg.member.displayName}`, msg.author.displayAvatarURL())
                                            .setTimestamp(msg.createdTimestamp)

                                        // Attach image/video if the original message had one
                                        if (msg.attachments) {
                                            if (msg.attachments.length >= 1) {
                                                msg.attachments.forEach(att => {
                                                    embed.attachFiles(att.attachment)
                                                })
                                            } else {
                                                msg.attachments.forEach(att => {
                                                    if (att.name.slice(att.name.length - 3) !== 'mp4') {
                                                        embed.attachFiles(att.attachment)
                                                        embed.setImage(`attachment://${att.name}`)
                                                    } else {
                                                        embed.attachFiles(att.attachment)
                                                    }
                                                })
                                            }
                                        }

                                        client.channels.cache.get(db.data.settings.archive).send(embed)
                                    } else {
                                        await msg.fetch()
                                        message.channel.send('This message was in `PARTIAL` format. We\'ve attempted to upgrade it to a full instance message. Try running the `forcearchive` command again and see if the message is send to the archive channel.')
                                    }
                                })
                            } else {
                                message.channel.send(`AutoDelete needs to be enabled for this channel before the archive function is made available. Ask an administrator to use the command \`!adx channel add ${message.channel.id} [timeout minutes]\`.`)
                            }
                            break
                        default:
                            message.channel.send('Unknown command. Type `!adx help` for command reference.')
                    }
                } else {
                    message.channel.send(`Sorry <@${message.author.id}>, you don't have *Administrator* permissions on this server and so cannot use \`!adx\` commands.`)
                }
                break
            case 'archive':
                if (db.data.settings.channels.includes(message.channel.id)) {
                    message.channel.messages.fetch({ limit: 1 }).then(messages => {
                        messages.forEach(msg => {
                            if (msg.reference) {
                                message.channel.messages.fetch(msg.reference.messageID).then(m => {
                                    if (db.data.settings.archive !== '') {
                                        if (m.cleanContent.length >= 2048) {
                                            message.channel.send('Oops, AutoDelete doesn\'t yet support messages longer than 2048 characters.')
                                        } else {
                                            // Create a new message embed
                                            const embed = new Discord.MessageEmbed()
                                                .setAuthor(m.member.displayName, m.author.displayAvatarURL())
                                                .setDescription(m.content)
                                                .setFooter(`Archived by ${msg.member.displayName}`, msg.author.displayAvatarURL())
                                                .setTimestamp(m.createdTimestamp)

                                            // Attach image/video if the original message had one
                                            if (m.attachments) {
                                                if (m.attachments.length >= 1) {
                                                    m.attachments.forEach(att => {
                                                        embed.attachFiles(att.attachment)
                                                    })
                                                } else {
                                                    m.attachments.forEach(att => {
                                                        if (att.name.slice(att.name.length - 3) !== 'mp4') {
                                                            embed.attachFiles(att.attachment)
                                                            embed.setImage(`attachment://${att.name}`)
                                                        } else {
                                                            embed.attachFiles(att.attachment)
                                                        }
                                                    })
                                                }
                                            }

                                            client.channels.cache.get(db.data.settings.archive).send(embed)
                                        }
                                    } else {
                                        message.channel.send('An administrator needs to set up the channel to be used for archiving messages. Ask them to use the command `!adx archive set [channel ID]`.')
                                    }
                                })
                                message.delete()
                            } else {
                                message.channel.send('Please use the *Reply* function with this command to archive a message.')
                            }
                        })
                    })
                } else {
                    message.channel.send(`AutoDelete needs to be enabled for this channel before the archive function is made available. Ask an administrator to use the command \`!adx channel add ${message.channel.id} [timeout minutes]\`.`)
                }
                break
            case 'ad':
                switch (args[0]) {
                    case 'help':
                        message.channel.send(
                            `*AutoDelete can now help you save important messages from temporary channels, great for keeping a record of something you don't want to lose.*\n\nHow do you do this? It's simple. **Simply reply to your message with \`!archive\` and AutoDelete will save it in <#${db.data.settings.archive}>.**\n\nFor server administrators, there is a suite of commands that can now help you manage AutoDelete across multiple channels. Use \`!adx help\` for more information.`
                        )
                        break
                }
                break
            default:
                break
        }
    }
});

// Spin up a basic HTML front-end page.
import http from 'http'
const server = http.createServer((request, response) => {
    response.writeHead(200, {"Content-Type": "text/plain"})
    response.end(`Hi, I'm AutoDelete!`)
});
const port = process.env.PORT || 1337
server.listen(port)