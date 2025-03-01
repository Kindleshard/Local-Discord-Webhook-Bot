"""
YouTube Topic IDs
This file contains common YouTube topic IDs and their human-readable names
Topic IDs are based on the Google Knowledge Graph
"""

# A dictionary of common YouTube topic IDs
# Key: Friendly name, Value: Topic ID
TOPIC_IDS = {
    "Gaming": "/m/0bzvm2",
    "Action Game": "/m/02ntfj",
    "Puzzle Video Game": "/m/04qvtq",
    "Role-playing Video Game": "/m/0403l3g",
    "Music": "/m/04rlf",
    "Pop Music": "/m/064t9",
    "Rock Music": "/m/06by7",
    "Hip Hop Music": "/m/0glt670",
    "Electronic Music": "/m/02lkt",
    "Technology": "/m/07c1v",
    "Software": "/m/01mf0",
    "Computer Hardware": "/m/01mfj",
    "Artificial Intelligence": "/m/0mkz",
    "Science": "/m/06ms67",
    "Physics": "/m/05qjc",
    "Chemistry": "/m/01n32",
    "Biology": "/m/01lq5c",
    "Education": "/m/0kpv11",
    "Sports": "/m/06ntj",
    "Football": "/m/02vx4",
    "Basketball": "/m/018jz",
    "Entertainment": "/m/02jjt",
    "Film": "/m/02vxn",
    "Television Program": "/m/0f2f9",
    "Comedy": "/m/09kqc",
    "News": "/m/05jxq",
    "Politics": "/m/05qt0",
    "Business": "/m/09s1f",
    "Finance": "/m/02_7x",
    "Fashion": "/m/032tl",
    "Food": "/m/02wbm",
    "Travel": "/m/07bxq",
    "Automotive": "/m/0k4j",
    "Fitness": "/m/027x7n",
    "Beauty": "/m/041xxh",
    "DIY & Crafts": "/m/01mqfj",
    "Animals": "/m/068hy",
    "Nature": "/m/05s2s",
}

# Topic IDs organized by category
TOPIC_CATEGORIES = {
    "Gaming": [
        {"name": "Gaming (All)", "id": "/m/0bzvm2"},
        {"name": "Action Games", "id": "/m/02ntfj"},
        {"name": "Puzzle Games", "id": "/m/04qvtq"},
        {"name": "RPG Games", "id": "/m/0403l3g"},
        {"name": "Strategy Games", "id": "/m/021bp2"},
        {"name": "Simulation Games", "id": "/m/04q1x3q"}
    ],
    "Music": [
        {"name": "Music (All)", "id": "/m/04rlf"},
        {"name": "Pop Music", "id": "/m/064t9"},
        {"name": "Rock Music", "id": "/m/06by7"},
        {"name": "Hip Hop", "id": "/m/0glt670"},
        {"name": "Electronic Music", "id": "/m/02lkt"},
        {"name": "Classical Music", "id": "/m/0ggq0m"}
    ],
    "Technology": [
        {"name": "Technology (All)", "id": "/m/07c1v"},
        {"name": "Software", "id": "/m/01mf0"},
        {"name": "Computer Hardware", "id": "/m/01mfj"},
        {"name": "Artificial Intelligence", "id": "/m/0mkz"},
        {"name": "Programming", "id": "/m/05z1_"}
    ],
    "Science": [
        {"name": "Science (All)", "id": "/m/06ms67"},
        {"name": "Physics", "id": "/m/05qjc"},
        {"name": "Chemistry", "id": "/m/01n32"},
        {"name": "Biology", "id": "/m/01lq5c"},
        {"name": "Astronomy", "id": "/m/01k8wb"}
    ],
    "Entertainment": [
        {"name": "Entertainment (All)", "id": "/m/02jjt"},
        {"name": "Film", "id": "/m/02vxn"},
        {"name": "Television", "id": "/m/0f2f9"},
        {"name": "Comedy", "id": "/m/09kqc"},
        {"name": "Animation", "id": "/m/0jxy"}
    ],
    "Lifestyle": [
        {"name": "Fashion", "id": "/m/032tl"},
        {"name": "Food", "id": "/m/02wbm"},
        {"name": "Travel", "id": "/m/07bxq"},
        {"name": "Fitness", "id": "/m/027x7n"},
        {"name": "Beauty", "id": "/m/041xxh"}
    ]
}

# Order parameters for search results
ORDER_OPTIONS = [
    {"name": "Relevance", "value": "relevance"},
    {"name": "Date (Newest)", "value": "date"},
    {"name": "View Count", "value": "viewCount"},
    {"name": "Rating", "value": "rating"},
    {"name": "Title", "value": "title"}
]
