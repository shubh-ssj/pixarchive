"""
Fast URL → site detection without importing gallery-dl.
Matches against known URL patterns for all supported sites.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SiteMatch:
    name: str
    url: str
    capabilities: str
    auth_type: Optional[str]
    category: str


# Pattern → (name, url, capabilities, auth_type, category)
# Ordered: more-specific patterns first
_PATTERNS: list[tuple[str, str, str, str, Optional[str], str]] = [
    # Pixiv ecosystem
    (r"pixiv\.net/novel",          "pixiv Novels",   "https://www.pixiv.net/novel", "Bookmarks, Novels, Series",                         "oauth",     "Pixiv Ecosystem"),
    (r"fanbox\.cc|pixiv\.net/fanbox","pixivFANBOX", "https://www.fanbox.cc/",      "Creators, Posts, Tag Searches",                      "cookies",   "Pixiv Ecosystem"),
    (r"pixiv\.net",                "pixiv",          "https://www.pixiv.net/",      "Artworks, Favorites, Follows, Rankings, Search",     "oauth",     "Pixiv Ecosystem"),
    # Social
    (r"bsky\.app",                 "Bluesky",        "https://bsky.app/",           "Posts, Feeds, Hashtags, Liked, User Profiles",       "supported", "Social Media"),
    (r"instagram\.com",            "Instagram",      "https://www.instagram.com/",  "Posts, Reels, Stories, Highlights, Tagged",          "cookies",   "Social Media"),
    (r"pinterest\.(com|ca|co\.uk)","Pinterest",      "https://www.pinterest.com/",  "All Pins, Boards, Search Results",                   "cookies",   "Social Media"),
    (r"reddit\.com",               "Reddit",         "https://www.reddit.com/",     "Submissions, Subreddits, User Profiles",              "oauth",     "Social Media"),
    (r"tumblr\.com",               "Tumblr",         "https://www.tumblr.com/",     "Blogs, Likes, Posts, Tag Searches",                  "oauth",     "Social Media"),
    (r"(x|twitter)\.com",         "Twitter/X",       "https://x.com/",              "Bookmarks, Likes, Media, Timelines, User Profiles",  "cookies",   "Social Media"),
    (r"facebook\.com",             "Facebook",       "https://www.facebook.com/",   "Albums, Photos, Videos, User Profiles",              "cookies",   "Social Media"),
    (r"bilibili\.com",             "Bilibili",       "https://www.bilibili.com/",   "Articles, User Articles",                            None,        "Social Media"),
    # Art platforms
    (r"artstation\.com",           "ArtStation",     "https://www.artstation.com/", "Albums, Collections, Likes, Search, User Profiles",  None,        "Art Platforms"),
    (r"deviantart\.com",           "DeviantArt",     "https://www.deviantart.com/","Collections, Deviations, Galleries, Tag Searches",   "oauth",     "Art Platforms"),
    (r"flickr\.com",               "Flickr",         "https://www.flickr.com/",     "Albums, Favorites, Galleries, Groups, Search",       "oauth",     "Art Platforms"),
    (r"newgrounds\.com",           "Newgrounds",     "https://www.newgrounds.com/", "Art, Audio, Favorites, Movies, User Profiles",       "supported", "Art Platforms"),
    (r"behance\.net",              "Behance",        "https://www.behance.net/",    "Collections, Galleries, User Profiles",              None,        "Art Platforms"),
    (r"itaku\.ee",                 "Itaku",          "https://itaku.ee/",           "Galleries, Posts, Search, Stars",                    None,        "Art Platforms"),
    (r"skeb\.jp",                  "Skeb",           "https://skeb.jp/",            "Posts, Works, User Profiles",                        None,        "Art Platforms"),
    (r"pillowfort\.social",        "Pillowfort",     "https://www.pillowfort.social/","Posts, User Profiles",                            "supported", "Art Platforms"),
    (r"500px\.com",                "500px",          "https://500px.com/",          "Favorites, Galleries, User Profiles",                None,        "Photography"),
    (r"smugmug\.com",              "SmugMug",        "https://www.smugmug.com/",    "Albums, Folders, User Profiles",                     "oauth",     "Photography"),
    (r"pexels\.com",               "Pexels",         "https://pexels.com/",         "Collections, Images, Search, User Profiles",         None,        "Photography"),
    # Creator/Patreon
    (r"patreon\.com",              "Patreon",        "https://www.patreon.com/",    "Collections, Creators, Posts",                       "cookies",   "Creator / Patreon-style"),
    (r"subscribestar\.com",        "SubscribeStar",  "https://www.subscribestar.com/","Posts, User Profiles",                            "supported", "Creator / Patreon-style"),
    (r"fantia\.jp",                "Fantia",         "https://fantia.jp/",          "Creators, Posts, Supported Creators",                "cookies",   "Creator / Patreon-style"),
    (r"boosty\.to",                "Boosty",         "https://www.boosty.to/",      "Posts, Subscriptions Feed, User Profiles",           "cookies",   "Creator / Patreon-style"),
    # Imageboards
    (r"danbooru\.donmai\.us",      "Danbooru",       "https://danbooru.donmai.us/",  "Pools, Posts, Tag Searches, User Profiles",          "supported", "Imageboards"),
    (r"e621\.net",                 "e621",           "https://e621.net/",            "Favorites, Pools, Posts, Tag Searches",               "supported", "Imageboards"),
    (r"e926\.net",                 "e926",           "https://e926.net/",            "Favorites, Pools, Posts (SFW), Tag Searches",         "supported", "Imageboards"),
    (r"gelbooru\.com",             "Gelbooru",       "https://gelbooru.com/",        "Pools, Posts, Tag Searches",                          "supported", "Imageboards"),
    (r"rule34\.xxx",               "Rule34",         "https://rule34.xxx/",          "Pools, Posts, Tag Searches",                          None,        "Imageboards"),
    (r"rule34\.paheal\.net",       "rule34.paheal",  "https://rule34.paheal.net/",   "Posts, Tag Searches",                                 None,        "Imageboards"),
    (r"safebooru\.org",            "Safebooru",      "https://safebooru.org/",       "Posts, Tag Searches",                                 None,        "Imageboards"),
    (r"konachan\.(com|net)",       "Konachan",       "https://konachan.com/",        "Pools, Posts, Tag Searches",                          "supported", "Imageboards"),
    (r"yande\.re",                 "yande.re",       "https://yande.re/",            "Pools, Posts, Tag Searches",                          "supported", "Imageboards"),
    (r"chan\.sankakucomplex\.com",  "Sankaku Chan",   "https://chan.sankakucomplex.com/","Pools, Posts, Tag Searches",                       "supported", "Imageboards"),
    (r"idol\.sankakucomplex\.com", "Sankaku Idol",   "https://idol.sankakucomplex.com/","Posts, Tag Searches",                              "supported", "Imageboards"),
    (r"zerochan\.net",             "Zerochan",       "https://www.zerochan.net/",    "Posts, Tag Searches, User Profiles",                  "supported", "Imageboards"),
    (r"3dbooru\.donatello\.us",    "3dbooru",        "https://3dbooru.donatello.us/","Pools, Posts, Tag Searches",                          None,        "Imageboards"),
    (r"tbib\.org",                 "TBIB",           "https://tbib.org/",            "Posts, Tag Searches",                                 None,        "Imageboards"),
    # Manga
    (r"mangadex\.org",             "MangaDex",       "https://mangadex.org/",       "Chapters, Covers, Library, MDLists, Manga",          "supported", "Manga / Comics"),
    (r"mangapark\.net",            "MangaPark",      "https://mangapark.net/",      "Chapters, Manga",                                    None,        "Manga / Comics"),
    (r"mangafire\.to",             "MangaFire",      "https://mangafire.to/",       "Chapters, Manga",                                    None,        "Manga / Comics"),
    (r"mangareader\.to",           "MangaReader",    "https://mangareader.to/",     "Chapters, Manga",                                    None,        "Manga / Comics"),
    (r"comick\.io",                "Comick",         "https://comick.io/",          "Chapters, Covers, Manga",                            None,        "Manga / Comics"),
    (r"dynasty-scans\.com",        "Dynasty Reader", "https://dynasty-scans.com/",  "Anthologies, Chapters, Manga, Search",               None,        "Manga / Comics"),
    (r"tapas\.io",                 "Tapas",          "https://tapas.io/",           "Creators, Episodes, Series",                         "supported", "Manga / Comics"),
    (r"comic\.naver\.com",         "Naver Webtoon",  "https://comic.naver.com/",    "Comics, Episodes",                                   None,        "Manga / Comics"),
    (r"readcomiconline\.",         "Read Comic Online","https://readcomiconline.li/","Comic Issues, Comics, Tag Searches",                 None,        "Manga / Comics"),
    # Image hosts
    (r"imgur\.com",                "imgur",          "https://imgur.com/",          "Albums, Favorites, Galleries, Search, User Profiles",None,        "Image Hosts / File Sharing"),
    (r"imgbb\.com",                "ImgBB",          "https://imgbb.com/",          "Albums, Images, User Profiles",                      "supported", "Image Hosts / File Sharing"),
    (r"bunkr\.(si|is|la|to)",      "Bunkr",          "https://bunkr.si/",           "Albums, Media Files",                                None,        "Image Hosts / File Sharing"),
    (r"cyberdrop\.(me|cr|nl)",     "Cyberdrop",      "https://cyberdrop.cr/",       "Albums, Media Files",                                None,        "Image Hosts / File Sharing"),
    (r"gofile\.io",                "Gofile",         "https://gofile.io/",          "Folders",                                            None,        "Image Hosts / File Sharing"),
    (r"catbox\.moe",               "Catbox",         "https://catbox.moe/",         "Albums, Files",                                      None,        "Image Hosts / File Sharing"),
    (r"pixeldrain\.com",           "pixeldrain",     "https://pixeldrain.com/",     "Albums, Files, Filesystems",                         None,        "Image Hosts / File Sharing"),
    (r"imgbox\.com",               "imgbox",         "https://imgbox.com/",         "Galleries, individual Images",                       None,        "Image Hosts / File Sharing"),
    # Japanese
    (r"seiga\.nicovideo\.jp",      "Niconico Seiga", "https://seiga.nicovideo.jp/", "Images, User Profiles",                              "supported", "Japanese Sites"),
    (r"iwara\.tv",                 "Iwara",          "https://www.iwara.tv/",       "Favorites, Playlists, Search, Videos",               "supported", "Japanese Sites"),
    (r"booth\.pm",                 "BOOTH",          "https://booth.pm/",           "Item Categories, Items, Shops",                      None,        "Japanese Sites"),
    # Other
    (r"discord\.com",              "Discord",        "https://discord.com/",        "Channels, DMs, Messages, Servers",                   None,        "Other / Misc"),
    (r"telegra\.ph",               "Telegraph",      "https://telegra.ph/",         "Galleries",                                          None,        "Other / Misc"),
    (r"civitai\.com",              "Civitai",        "https://www.civitai.com/",    "Collections, Images, Models, Posts, Search",         None,        "Photography"),
    (r"lexica\.art",               "Lexica",         "https://lexica.art/",         "Search Results",                                     None,        "Photography"),
    (r"soundgasm\.net",            "Soundgasm",      "https://soundgasm.net/",      "Audio, User Profiles",                               None,        "Other / Misc"),
    (r"steamgriddb\.com",          "SteamGridDB",    "https://www.steamgriddb.com", "Grids, Heroes, Icons, Logos",                        None,        "Other / Misc"),
    (r"archiveofourown\.org",      "Archive of Our Own","https://archiveofourown.org/","Works, Series, User Profiles",                    "supported", "Other / Misc"),
    (r"itch\.io",                  "itch.io",        "https://itch.io/",            "Games",                                              None,        "Other / Misc"),
    (r"4chan\.org",                 "4chan",          "https://www.4chan.org/",      "Boards, Threads",                                    None,        "Forums / Boards"),
]

_COMPILED = [(re.compile(pat, re.IGNORECASE), *rest) for pat, *rest in _PATTERNS]


def detect_site(url: str) -> Optional[SiteMatch]:
    """Return a SiteMatch if the URL matches a known gallery-dl extractor, else None."""
    url = url.strip()
    if not url:
        return None
    for pat, name, site_url, caps, auth, cat in _COMPILED:
        if pat.search(url):
            return SiteMatch(name=name, url=site_url, capabilities=caps,
                             auth_type=auth, category=cat)
    return None


AUTH_LABELS = {
    "oauth":     ("OAuth",    "#1e3a5f", "#89b4fa"),
    "cookies":   ("Cookies",  "#2a2010", "#f9e2af"),
    "required":  ("Required", "#3a1e1e", "#f38ba8"),
    "supported": ("Optional", "#1e3a2f", "#a6e3a1"),
    None:        ("Public",   "#252530", "#6c7086"),
}
