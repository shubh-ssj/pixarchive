"""
Full list of gallery-dl supported sites, sourced from:
https://gdl-org.github.io/docs/supportedsites.html

Each entry: (name, url, capabilities, auth_type)
auth_type: None | "oauth" | "cookies" | "required" | "supported"
"""

SUPPORTED_SITES = [
    # ── Social Media ──────────────────────────────────────────────────────────
    ("Bluesky",         "https://bsky.app/",               "Avatars, Bookmarks, Feeds, Followed Users, Hashtags, Likes, Lists, Posts, Replies, Search, Videos",  "supported"),
    ("Facebook",        "https://www.facebook.com/",       "Albums, Avatars, Photos, Profile Photos, Sets, User Profiles, Videos",                                 "cookies"),
    ("Instagram",       "https://www.instagram.com/",      "Collections, Followers, Highlights, Posts, Reels, Saved Posts, Stories, Tag Searches, Tagged Posts",   "cookies"),
    ("Pinterest",       "https://www.pinterest.com/",      "All Pins, Created Pins, Pins, pin.it Links, Related Pins, Search Results, Sections",                   "cookies"),
    ("Reddit",          "https://www.reddit.com/",         "Home Feed, individual Images, Redirects, Submissions, Subreddits, User Profiles",                       "oauth"),
    ("Tumblr",          "https://www.tumblr.com/",         "Blogs, Likes, Notifications, Posts, Searches, Followed Users, Tag Searches",                            "oauth"),
    ("Twitter/X",       "https://x.com/",                  "Bookmarks, Likes, Lists, Media, Replies, Retweets, Search Results, Timelines, User Profiles",           "cookies"),
    ("Plurk",           "https://www.plurk.com/",          "Posts, Timelines",                                                                                      None),
    ("Arcalive",        "https://arca.live/",              "Boards, Posts, User Posts",                                                                             None),
    ("Bilibili",        "https://www.bilibili.com/",       "Articles, User Articles, User Article Favorites",                                                       None),

    # ── Art Platforms ─────────────────────────────────────────────────────────
    ("ArtStation",      "https://www.artstation.com/",     "Albums, Artwork Listings, Challenges, Collections, Followed Users, Likes, Search Results",              None),
    ("Behance",         "https://www.behance.net/",        "Collections, Galleries, User Profiles",                                                                 None),
    ("DeviantArt",      "https://www.deviantart.com/",     "Avatars, Collections, Deviations, Favorites, Folders, Galleries, Journals, Search, Tag Searches",       "oauth"),
    ("Flickr",          "https://www.flickr.com/",         "Albums, Favorites, Galleries, Groups, individual Images, Search Results, User Profiles",                 "oauth"),
    ("Itaku",           "https://itaku.ee/",               "Bookmarks, Followers, Followed Users, Galleries, Posts, Search Results, Stars",                         None),
    ("Newgrounds",      "https://www.newgrounds.com/",     "Art, Audio, Favorites, Followed Users, Games, Movies, Search Results",                                   "supported"),
    ("Pillowfort",      "https://www.pillowfort.social/",  "Posts, User Profiles",                                                                                  "supported"),
    ("Poipiku",         "https://poipiku.com/",            "Posts, User Profiles",                                                                                  "supported"),
    ("Skeb",            "https://skeb.jp/",                "Followed Creators, Posts, Search Results, Sent Requests, Works",                                         None),
    ("Piczel",          "https://piczel.tv/",              "Folders, individual Images, User Profiles",                                                             None),
    ("Picarto",         "https://picarto.tv/",             "Galleries",                                                                                             None),
    ("foriio",          "https://foriio.com/",             "User Profiles, Works",                                                                                  None),
    ("Audiochan",       "https://audiochan.com/",          "Audios, Collections, Search Results, User Profiles",                                                    None),
    ("Adobe Portfolio", "https://www.myportfolio.com/",   "Galleries",                                                                                             None),
    ("Desktopography",  "https://desktopography.net/",    "Entries, Exhibitions",                                                                                  None),
    ("Architizer",      "https://architizer.com/",         "Firms, Projects",                                                                                       None),

    # ── Pixiv Ecosystem ───────────────────────────────────────────────────────
    ("pixiv",           "https://www.pixiv.net/",          "Artworks, Avatars, Favorites, Follows, pixivision, Rankings, Search Results, Series, User Profiles",    "oauth"),
    ("pixiv Novels",    "https://www.pixiv.net/novel",     "Bookmarks, Novels, Series, User Profiles",                                                              "oauth"),
    ("pixivFANBOX",    "https://www.fanbox.cc/",          "Creators, Home Feed, Posts, Pixiv Redirects, Tag Searches",                                              "cookies"),

    # ── Creator / Patreon-style ───────────────────────────────────────────────
    ("Patreon",         "https://www.patreon.com/",        "Collections, Creators, Posts, User Profiles",                                                            "cookies"),
    ("SubscribeStar",   "https://www.subscribestar.com/",  "Posts, User Profiles",                                                                                  "supported"),
    ("Fantia",          "https://fantia.jp/",              "Creators, Posts, Supported Creators",                                                                   "cookies"),
    ("Boosty",          "https://www.boosty.to/",          "DMs, Subscriptions Feed, Followed Users, Media Files, Posts",                                            "cookies"),
    ("Ci-en",           "https://ci-en.net/",              "Articles, Creators, Followed Users, Recent Images",                                                     None),

    # ── Imageboards / Booru ───────────────────────────────────────────────────
    ("Zerochan",        "https://www.zerochan.net/",       "Posts, Search Results, User Profiles",                                                                  "supported"),

    # ── Manga / Comics ────────────────────────────────────────────────────────
    ("MangaDex",        "https://mangadex.org/",           "Authors, Chapters, Covers, Updates Feed, Library, MDLists, Manga",                                     "supported"),
    ("MangaFire",       "https://mangafire.to/",           "Chapters, Manga",                                                                                       None),
    ("MangaPark",       "https://mangapark.net/",          "Chapters, Manga",                                                                                       None),
    ("MangaReader",     "https://mangareader.to/",         "Chapters, Manga",                                                                                       None),
    ("Comick",          "https://comick.io/",              "Chapters, Covers, Manga",                                                                               None),
    ("Dynasty Reader",  "https://dynasty-scans.com/",     "Anthologies, Chapters, individual Images, Manga, Search Results",                                       None),
    ("Madokami",        "https://manga.madokami.al/",      "Manga",                                                                                                 "required"),
    ("Manga Fox",       "https://fanfox.net/",             "Chapters, Manga",                                                                                       None),
    ("Manga Here",      "https://www.mangahere.cc/",       "Chapters, Manga",                                                                                       None),
    ("MangaFreak",      "https://ww2.mangafreak.me/",      "Chapters, Manga",                                                                                       None),
    ("MangaRead",       "https://mangaread.org/",          "Chapters, Manga",                                                                                       None),
    ("MangaTaro",       "https://mangataro.org/",          "Chapters, Manga",                                                                                       None),
    ("MangaTown",       "https://www.mangatown.com/",      "Chapters, Manga",                                                                                       None),
    ("Read Comic Online","https://readcomiconline.li/",    "Comic Issues, Comics, Tag Searches",                                                                    None),
    ("Naver Webtoon",   "https://comic.naver.com/",        "Comics, Episodes",                                                                                      None),
    ("Tapas",           "https://tapas.io/",               "Creators, Episodes, Series",                                                                            "supported"),
    ("Dandadan",        "https://dandadan.net/",           "Chapters, Manga",                                                                                       None),
    ("Danke fürs Lesen","https://danke.moe/",              "Chapters, Manga",                                                                                       None),
    ("Rawkuma",         "https://rawkuma.net/",            "Chapters, Manga",                                                                                       None),
    ("HiperDEX",        "https://hiperdex.com/",           "Artists, Chapters, Manga",                                                                              None),
    ("Komikcast",       "https://komikcast.li/",           "Chapters, Manga",                                                                                       None),
    ("KaliScan",        "https://kaliscan.me/",            "Chapters, Manga",                                                                                       None),
    ("TCB Scans",       "https://tcbonepiecechapters.com/","Chapters, Manga",                                                                                       None),
    ("Sen Manga",       "https://raw.senmanga.com/",       "Chapters",                                                                                              None),
    ("Keenspot",        "http://www.keenspot.com/",        "Comics",                                                                                                None),

    # ── Image Hosts / File Sharing ────────────────────────────────────────────
    ("imgur",           "https://imgur.com/",              "Albums, Favorites, Galleries, individual Images, Personal Posts, Search Results",                       None),
    ("ImgBB",           "https://imgbb.com/",              "Albums, individual Images, User Profiles",                                                              "supported"),
    ("imgbox",          "https://imgbox.com/",             "Galleries, individual Images",                                                                          None),
    ("ImageBam",        "https://www.imagebam.com/",       "Galleries, individual Images",                                                                          None),
    ("ImageShack",      "https://imageshack.com/",         "Galleries, individual Images, User Profiles",                                                           None),
    ("ImageChest",      "https://imgchest.com/",           "Galleries, User Profiles",                                                                              None),
    ("ImagePond",       "https://www.imagepond.net/",      "Albums, Files, User Profiles",                                                                          None),
    ("imgpile",         "https://imgpile.com/",            "Posts, User Profiles",                                                                                  None),
    ("Lensdump",        "https://lensdump.com/",           "Albums, individual Images",                                                                             None),
    ("Gofile",          "https://gofile.io/",              "Folders",                                                                                               None),
    ("Catbox",          "https://catbox.moe/",             "Albums, Files",                                                                                         None),
    ("Bunkr",           "https://bunkr.si/",               "Albums, Media Files",                                                                                   None),
    ("Cyberdrop",       "https://cyberdrop.cr/",           "Albums, Media Files",                                                                                   None),
    ("CyberFile",       "https://cyberfile.me/",           "Files, Folders, Shares",                                                                                None),
    ("MixDrop",         "https://mixdrop.ag/",             "Files",                                                                                                 None),
    ("pixeldrain",      "https://pixeldrain.com/",         "Albums, Files, Filesystems",                                                                            None),
    ("Koofr",           "https://koofr.net/",              "Shared Links",                                                                                          None),
    ("imgth",           "https://imgth.com/",              "Galleries",                                                                                             None),
    ("SlickPic",        "https://www.slickpic.com/",       "Albums, User Profiles",                                                                                 None),
    ("S3ND",            "https://s3nd.pics/",              "Posts, Search Results, User Profiles",                                                                  None),
    ("filester.me",     "https://filester.me/",            "Files, Folders",                                                                                        None),

    # ── Photography ───────────────────────────────────────────────────────────
    ("500px",           "https://500px.com/",              "Favorites, Galleries, individual Images, User Profiles",                                                 None),
    ("35PHOTO",         "https://35photo.pro/",            "Genres, individual Images, Tag Searches, User Profiles",                                                 None),
    ("Pexels",          "https://pexels.com/",             "Collections, individual Images, Search Results, User Profiles",                                          None),
    ("SmugMug",         "https://www.smugmug.com/",        "Albums, individual Images, Images from Users and Folders",                                               "oauth"),
    ("Lightroom",       "https://lightroom.adobe.com/",   "Galleries",                                                                                             None),
    ("Issuu",           "https://issuu.com/",              "Publications, User Profiles",                                                                           None),
    ("Lexica",          "https://lexica.art/",             "Search Results",                                                                                        None),
    ("Civitai",         "https://www.civitai.com/",        "Collections, Images, Models, Posts, Search Results, Tag Searches, User Profiles",                       None),

    # ── Forums / Boards ───────────────────────────────────────────────────────
    ("4chan",           "https://www.4chan.org/",           "Boards, Threads",                                                                                       None),
    ("JoyReactor",      "https://joyreactor.com/",          "Posts, Search Results, Tag Searches, User Profiles",                                                    None),
    ("pholder",         "https://pholder.com/",             "Search Results, Subreddits, User Profiles",                                                             None),

    # ── Japanese Sites ────────────────────────────────────────────────────────
    ("Niconico Seiga",  "https://seiga.nicovideo.jp/",      "individual Images, User Profiles",                                                                      "supported"),
    ("Iwara",           "https://www.iwara.tv/",            "Favorites, Followers, Followed Users, Playlists, Search Results, User Profiles, Videos",               "supported"),
    ("HatenaBlog",      "https://hatenablog.com",           "Archive, Individual Posts, Home Feed, Search Results",                                                  None),
    ("Naver Blog",      "https://blog.naver.com/",          "Blogs, Posts",                                                                                          None),
    ("CHZZK",           "https://chzzk.naver.com/",         "Comments, Communities",                                                                                 None),
    ("LOFTER",          "https://www.lofter.com/",          "Blog Posts, Posts",                                                                                     None),
    ("livedoor Blog",   "http://blog.livedoor.jp/",         "Blogs, Posts",                                                                                          None),
    ("BOOTH",           "https://booth.pm/",                "Item Categories, Items, Shops",                                                                         None),
    ("Mangoxo",         "https://www.mangoxo.com/",         "Albums, Channels",                                                                                      "supported"),
    ("Pixnet",          "https://www.pixnet.net/",          "Folders, individual Images, Sets, User Profiles",                                                       None),


    # ── Other / Misc ─────────────────────────────────────────────────────────
    ("Archive of Our Own","https://archiveofourown.org/",  "Search Results, Series, Tag Searches, User Profiles, User Works, Works",                                "supported"),
    ("Are.na",          "https://are.na/",                  "Channels",                                                                                              None),
    ("BBC",             "https://bbc.co.uk/",               "Galleries, Programmes",                                                                                 None),
    ("Comic Art Fans",  "https://www.comicartfans.com/",    "Artists, Artworks, Galleries, Search Results",                                                          None),
    ("Comic Vine",      "https://comicvine.gamespot.com/",  "Tag Searches",                                                                                          None),
    ("Comedy Wildlife", "https://www.comedywildlifephoto.com/","Galleries",                                                                                         None),
    ("Discord",         "https://discord.com/",             "Channels, DMs, Messages, Servers, Server Assets, Server Searches",                                     None),
    ("Khinsider",       "https://downloads.khinsider.com/", "Soundtracks",                                                                                          None),
    ("Listal",          "https://listal.com",               "individual Images, People",                                                                             None),
    ("PhotoVogue",      "https://www.vogue.com/photovogue/","User Profiles",                                                                                        None),
    ("Soundgasm",       "https://soundgasm.net/",           "Audio, User Profiles",                                                                                  None),
    ("Speaker Deck",    "https://speakerdeck.com/",         "Presentations",                                                                                         None),
    ("SlideShare",      "https://www.slideshare.net/",      "Presentations",                                                                                         None),
    ("SteamGridDB",     "https://www.steamgriddb.com",      "Individual Assets, Grids, Heroes, Icons, Logos",                                                       None),
    ("Telegraph",       "https://telegra.ph/",              "Galleries",                                                                                             None),
    ("Tenor",           "https://tenor.com/",               "individual Images",                                                                                     None),
    ("itch.io",         "https://itch.io/",                 "Games",                                                                                                 None),
]

CATEGORIES = [
    "All",
    "Social Media",
    "Art Platforms",
    "Pixiv Ecosystem",
    "Creator / Patreon-style",
    "Imageboards / Booru",
    "Manga / Comics",
    "Image Hosts / File Sharing",
    "Photography",
    "Forums / Boards",
    "Japanese Sites",
    "Other / Misc",
]

# Map site name → category for quick lookup
SITE_CATEGORIES: dict[str, str] = {
    "Bluesky": "Social Media", "Facebook": "Social Media", "Instagram": "Social Media",
    "Pinterest": "Social Media", "Reddit": "Social Media", "Tumblr": "Social Media",
    "Twitter/X": "Social Media", "Plurk": "Social Media", "Arcalive": "Social Media",
    "Bilibili": "Social Media", 
    "ArtStation": "Art Platforms", "Behance": "Art Platforms", "DeviantArt": "Art Platforms",
    "Flickr": "Art Platforms", 
    "Itaku": "Art Platforms", "Newgrounds": "Art Platforms",
    "Pillowfort": "Art Platforms", "Poipiku": "Art Platforms", "Skeb": "Art Platforms",
    "Piczel": "Art Platforms", "Picarto": "Art Platforms", "foriio": "Art Platforms",
    "Audiochan": "Art Platforms", "Adobe Portfolio": "Art Platforms",
    "Desktopography": "Art Platforms", "Architizer": "Art Platforms",
    "pixiv": "Pixiv Ecosystem", "pixiv Novels": "Pixiv Ecosystem", "pixivFANBOX": "Pixiv Ecosystem",
    "Patreon": "Creator / Patreon-style", "SubscribeStar": "Creator / Patreon-style",
    "Fantia": "Creator / Patreon-style", "Boosty": "Creator / Patreon-style",
    "Ci-en": "Creator / Patreon-style", 
    
    
    
    
    
    
    
    
    
    
    "Zerochan": "Imageboards / Booru",
    
    
    
    
    
    
    "MangaDex": "Manga / Comics", "MangaFire": "Manga / Comics",
    "MangaPark": "Manga / Comics", "MangaReader": "Manga / Comics",
    "Comick": "Manga / Comics", "Dynasty Reader": "Manga / Comics",
    "Madokami": "Manga / Comics", "Manga Fox": "Manga / Comics",
    "Manga Here": "Manga / Comics", "MangaFreak": "Manga / Comics",
    "MangaRead": "Manga / Comics", "MangaTaro": "Manga / Comics",
    "MangaTown": "Manga / Comics", "Read Comic Online": "Manga / Comics",
    "Naver Webtoon": "Manga / Comics", "Tapas": "Manga / Comics",
    "Dandadan": "Manga / Comics", "Danke fürs Lesen": "Manga / Comics",
    "Rawkuma": "Manga / Comics", "HiperDEX": "Manga / Comics",
    "Komikcast": "Manga / Comics", "KaliScan": "Manga / Comics",
    "TCB Scans": "Manga / Comics", "Sen Manga": "Manga / Comics",
    
    "Keenspot": "Manga / Comics",
    "imgur": "Image Hosts / File Sharing", 
    "ImgBB": "Image Hosts / File Sharing", "imgbox": "Image Hosts / File Sharing",
    "ImageBam": "Image Hosts / File Sharing", "ImageShack": "Image Hosts / File Sharing",
    "ImageChest": "Image Hosts / File Sharing", "ImagePond": "Image Hosts / File Sharing",
    "imgpile": "Image Hosts / File Sharing", "Lensdump": "Image Hosts / File Sharing",
    "Gofile": "Image Hosts / File Sharing", "Catbox": "Image Hosts / File Sharing",
    "Bunkr": "Image Hosts / File Sharing", "Cyberdrop": "Image Hosts / File Sharing",
    "CyberFile": "Image Hosts / File Sharing", "MixDrop": "Image Hosts / File Sharing",
    "pixeldrain": "Image Hosts / File Sharing", "Koofr": "Image Hosts / File Sharing",
    "imgth": "Image Hosts / File Sharing",
    
    "SlickPic": "Image Hosts / File Sharing", "S3ND": "Image Hosts / File Sharing",
    "filester.me": "Image Hosts / File Sharing",
    "500px": "Photography", "35PHOTO": "Photography", "Pexels": "Photography",
    "SmugMug": "Photography", "Lightroom": "Photography", "Issuu": "Photography",
    "Lexica": "Photography", "Civitai": "Photography",
    "4chan": "Forums / Boards", 
    
    
    "JoyReactor": "Forums / Boards", "pholder": "Forums / Boards",
    "Niconico Seiga": "Japanese Sites", "Iwara": "Japanese Sites",
    "HatenaBlog": "Japanese Sites", "Naver Blog": "Japanese Sites",
    "CHZZK": "Japanese Sites", "LOFTER": "Japanese Sites",
    "livedoor Blog": "Japanese Sites", "BOOTH": "Japanese Sites",
    "Mangoxo": "Japanese Sites", "Pixnet": "Japanese Sites",
}
