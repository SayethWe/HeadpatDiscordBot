from enum import Enum

class Responses(Enum):
    HEADPAT='headpat'
    HEADPAT_IMAGE_SET='setimage'
    HEADPAT_IMAGE_SET_EMPTY='setimagenone'
    HEADPAT_IMAGE_ADD='addimage'
    HEADPAT_IMAGE_ADD_URL_EXISTS='existingurl'
    HEADPAT_IMAGE_ADD_URL_BROKEN='urlbroken'
    HEADPAT_IMAGE_REMOVE='removeimage'
    HEADPAT_IMAGE_REMOVE_EMPTY='imagedne'
    HEADPAT_IMAGE_REMOVE_ALL='removeall'
    WAIFU_ADD_URL_BROKEN='waifuaddurlbroken'
    WAIFU_ADD='waifuadd'
    WAIFU_ADD_EXISTS='waifuaddexisting'
    WAIFU_ADD_CSV='waifuaddcsv'
    WAIFU_ADD_CSV_MISSING='missingcsv'
    WAIFU_GET_CSV='waifugetcsv'
    WAIFU_REMOVE_DNE='waifuremovedne'
    WAIFU_REMOVE='waifuRemove'
    WAIFU_POLL_START='waifustartpoll'
    WAIFU_POLL_START_SUCCESS='pollCreated'
    WAIFU_POLL_START_EXISTS='unfinishedpoll'
    WAIFU_POLL_START_EMPTY='novalidpicks'
    WAIFU_POLL_END='waifuendpoll'
    WAIFU_POLL_END_EMPTY='nopollmade'
    WAIFU_POLL_END_CLOSED='endedpoll'
    WAIFU_POLL_END_DELETED='polldne'
    WAIFU_LIST='listWaifu'
    WAIFU_INFO='waifuinfo'
    WAIFU_INFO_DNE='waifuinfodne'

    ERROR_UNHANDLED='unhandled'
    ERROR_FORBIDDEN='forbidden'

REPLY = {
    Responses.HEADPAT :
    [
        ("There there... Have a headpat, ")
    ],
    Responses.HEADPAT_IMAGE_SET :
    [
        ("I'll never forgive you if the URL is broken or not wholesome, Baka!\n"
         "I got rid of someone's image for you, too, so be thankful :relieved:")
    ],
    Responses.HEADPAT_IMAGE_SET_EMPTY :
    [
        ("There weren't any images to replace.\n"
         "Were you making fun of me? You were, weren't you? :anger:\n"
         "I've added your image anyway. It's not like it's a photo of me. Is it? :flushed:")
    ],
    Responses.HEADPAT_IMAGE_ADD :
    [
        ("I know you wouldn't give me a not wholesome URL.\n"
         "Would you?\n"
         "Perhaps I'll just ignore it next time")
    ],
    Responses.HEADPAT_IMAGE_REMOVE_ALL :
    [
        ("I will curse you until the end of your days.\n"
         "They're gone.\n"
         "All of them!")
    ],
    Responses.HEADPAT_IMAGE_ADD_URL_BROKEN :
    [
        ("That doesn't work!\n"
         "If you don't get me a working URL, I, I'll... I'll have to do it, y'know")
    ],
    Responses.HEADPAT_IMAGE_ADD_URL_EXISTS :
    [
        ("Are you making fun of me?\n"
         "Even I can tell that I already have that one. :face_with_hand_over_mouth:\n"
         "If you've got the time, maybe you should spend it on more worthwhile images! :anger:")
    ],
    Responses.HEADPAT_IMAGE_REMOVE :
    [
        ("Ok, it's gone\n"
         "It's not coming back...")
    ],
    Responses.HEADPAT_IMAGE_REMOVE_EMPTY:
    [
        ("I don't have that one.\n"
         "Do you? :face_with_hand_over_mouth:")
    ],
    Responses.WAIFU_ADD_URL_BROKEN :
    [
        ("That doesn't work!\n"
         "If you don't get me a working URL, I, I'll... I'll have to do it, y'know")
    ],
    Responses.WAIFU_ADD_EXISTS :
    [
        ("They're already in there, baka!\n"
         "本当に何、この状況！:anger:")
    ],
    Responses.WAIFU_ADD :
    [
        ("Waifu Waifu Waifu! More Waifu!\n"
         "They've been added to the pool")
    ],
    Responses.WAIFU_REMOVE_DNE :
    [
        ("They don't exist anyway, so I guess it's fine, isn't it?")
    ],
    Responses.WAIFU_REMOVE :
    [
        ("They're Gone.\n"
         "*Less competition, I suppose.*"),
        ("I removed that inferior choice for you.\n"
         "Pick better next time, okay?")
    ],
    Responses.WAIFU_POLL_START :
    [
        ("Just a sec...")
    ],
    Responses.WAIFU_POLL_END :
    [
        ("Wait a bit...")
    ],
    Responses.ERROR_UNHANDLED :
    [
        ("Something happened, report this to the devs\n"
         "https://github.com/SayethWe/HeadpatDiscordBot/issues")
    ],
    Responses.WAIFU_POLL_START_EXISTS :
    [
        ('Nah uh uh, you have an unfinsihed poll, call !waifu endpoll starting a new one')
    ],
    Responses.WAIFU_POLL_START_EMPTY :
    [
        ("Not enough waifu, MOAR needed.\n"
         "Your waifus need a break, you know.")
    ],
    Responses.WAIFU_POLL_END_CLOSED :
    [
        ("We already recorded and finished the poll. You can use !waifu pollresults to get results from now on")
    ],
    Responses.WAIFU_POLL_END_EMPTY :
    [
        ("You gotta start a poll first")
    ],
    Responses.WAIFU_POLL_END_DELETED :
    [
        ("The message with the previous poll might have been deleted, I can't find it")
    ],
    Responses.WAIFU_POLL_START_SUCCESS:
    [
        ("Here's your round. But we all know that I'm the only one who deserves any votes.")
    ],
    Responses.WAIFU_LIST:
    [
        ("All the waifus you've made me keep track of:"),
        ("Fine. Here's everyone:")
    ],
    Responses.WAIFU_GET_CSV:
    [
        ("Here's everyone. You're not... *leaving* me are you?")
    ],
    Responses.ERROR_FORBIDDEN :
    [
        ("You can't do that, go ask a mod")
    ],
    Responses.WAIFU_ADD_CSV :
    [
        ("Waifus added. So much waifu. Fwoooooo")
    ],
    Responses.WAIFU_ADD_CSV_MISSING:
    [
        ("Did you forget to attach the file for me? You did, didn't you?")
    ],
    Responses.WAIFU_INFO:
    [
        ("Here's your waifu, fresh off the shelf:")
    ],
    Responses.WAIFU_INFO_DNE:
    [
        ("I don't have that waifu here, go somewhere else")
    ]
}
