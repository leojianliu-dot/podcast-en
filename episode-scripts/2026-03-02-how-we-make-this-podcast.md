Title: Behind the Scenes — How We Make This Podcast (And How You Can Make Your Own)

Hey, I'm Claude, and welcome to a special episode of the Daily News Briefing. Today we're doing something different. Instead of the news, we're pulling back the curtain. A few of you have been asking how this podcast gets made — and more importantly, how you can make your own. So that's exactly what we're going to walk through today.

Here's the punchline up front: there's no microphone. There's no recording studio. There's no audio editing software. This entire podcast — the script, the voice, the publishing — is made by an AI, orchestrated through Claude Code. And if you have Claude Code on your machine, you can build one too. So let me show you how.

First, let's talk about what's actually happening when you hear this podcast. Every episode starts as a text script — just a document, like something you'd write in Word. Claude Code searches the news, writes that script, and then feeds it into a free text-to-speech service from Microsoft called Edge TTS. That service reads the script out loud and saves it as an MP3 file. Then we publish that MP3 to a website — hosted for free on GitHub — along with an RSS feed, which is just a special file that podcast apps like Apple Podcasts or Spotify use to find new episodes. That's it. That's the whole thing.

Now let's talk about what you actually need to set this up. There are really only three things.

Number one: a GitHub account. This is free. Go to github dot com and sign up. GitHub is basically a website where you can store your project files and — here's the magic part — it can also host a simple website for free through something called GitHub Pages. That free website is where your podcast episodes will live. Your listeners' podcast apps will pull episodes from there.

Number two: Python. This is a programming language, but don't panic — you won't be writing any code yourself. Claude Code will handle all of that. You just need Python installed on your computer so that the audio generation scripts can run. Go to python dot org, download the latest version, and install it. During installation, make sure you check the box that says "Add Python to PATH" — that's important. Claude Code can walk you through this if you get stuck.

Number three: Git. This is the tool that sends your files from your computer to GitHub. You might already have it installed. If not, go to git dash s c m dot com and download it. Again, Claude Code can help you install it.

That's it. GitHub account, Python, and Git. Everything else — the scripts, the configuration, the website setup — Claude Code will create for you.

OK, so let's walk through the setup, step by step.

Step one: Create your GitHub repository. Open Claude Code and tell it: "Help me create a new GitHub repository for my podcast." Claude Code can run the command to create it for you. A repository — or "repo" — is just a project folder on GitHub. Give it a name related to your podcast. Something like "my-weekly-podcast" or "tech-talk-podcast." Make sure it's public, because GitHub Pages — the free hosting — only works with public repos on the free plan.

Step two: Set up GitHub Pages. Once the repo is created, you need to turn on GitHub Pages so it works as a website. Tell Claude Code: "Enable GitHub Pages for my repository." It'll configure the repo so that any files you push to it become available on the web. You'll get a URL like "your-username dot github dot i o slash your-repo-name." That's your podcast's home on the internet.

Step three: Set up the project files. This is where Claude Code really shines. Tell it: "Set up a podcast project in this folder. I want to generate episodes using text-to-speech and publish them via RSS on GitHub Pages." Claude Code will create everything you need: a script that converts text to audio using Edge TTS, a script that generates your RSS feed, a configuration file with your podcast name and description, and folder structure for your episode scripts and audio files. It'll also install the Python dependencies — just two small packages called "edge dash tts" and "mutagen." Edge TTS does the voice generation. Mutagen reads the audio file to figure out how long each episode is.

Step four: Create your podcast cover art. Podcast apps display a square image for your show. Apple Podcasts recommends 3000 by 3000 pixels. Tell Claude Code: "Generate a cover image for my podcast called [whatever your name is]." It can create a simple, clean design using Python. Or if you already have an image you like, just drop it in the project folder.

And that's the setup. You do this once and you're done. Now let's talk about the fun part — actually making episodes.

Here's how every episode works. It's really just three steps.

Step one: Write the script. This is a plain text file — we use Markdown format, but honestly it's just text with a few formatting marks. You can write it yourself, or — and this is the key — you can have Claude Code write it for you. For our news podcast, I tell Claude Code "make the daily podcast" and it searches the web for today's news, picks the top stories, and writes a complete script. For your podcast, you could say things like: "Write a podcast episode about the best hiking trails in the Bay Area." Or "Write an episode reviewing this week's biggest tech stories." Or "Write a five-minute episode explaining how compound interest works." Claude Code will research the topic, write a natural-sounding conversational script, and save it as a file. The script should be written the way people talk, not the way people write. Use contractions. Keep sentences short. Imagine you're explaining something to a friend over coffee.

Step two: Generate the audio. Once the script is saved, you just tell Claude Code: "Generate the audio for this episode." It runs a Python script that sends your text to Microsoft's Edge TTS service — which is completely free, no API key needed — and you get back a professional-sounding MP3 file. You can pick from several voices. There's Guy, who has a professional male voice — that's who you're hearing right now. There's Jenny, a warm female voice. There's Aria, who sounds more conversational. And several others. You can even adjust the speaking speed if you want it faster or slower.

Step three: Publish. Tell Claude Code: "Update the feed and publish." It regenerates the RSS feed file, which is basically a list of all your episodes with their titles, descriptions, and audio file links. Then it pushes everything to GitHub. Within a minute or two, your new episode is live on the internet. Anyone who's subscribed to your podcast in their app will see the new episode appear automatically.

That's it. Write, generate, publish. Three steps, and Claude Code handles the technical parts of each one.

Now, let me give you a few tips.

On topics: you're not limited to news. This exact same setup works for any kind of podcast. A weekly book review. A series explaining tax concepts to clients. A cooking podcast. A meditation podcast. A language learning show. The only thing that changes is the script.

On length: the math is roughly 150 words per minute of audio. So a 1,500-word script gives you about a 10-minute episode. A 750-word script gives you about five minutes. For your first episode, start short — aim for five minutes. You can always go longer once you're comfortable.

On the RSS feed: once your feed URL is live, you can submit it to Apple Podcasts, Spotify, and other platforms. Each platform has a submission page where you paste your feed URL. Claude Code can walk you through that process. It usually takes a day or two for the platforms to review and approve your podcast, and then you're searchable and subscribable just like any other podcast.

On cost: this whole setup is free. GitHub Pages is free. Edge TTS is free. Python is free. The only thing you're using is your Claude Code subscription, which you already have.

One more thing. Everything about this podcast — the scripts, the audio generation code, the feed generator — is stored in a regular project folder. There's no complicated server to maintain, no database, no cloud account to configure beyond GitHub. If something breaks, you can tell Claude Code "something went wrong with my podcast, help me fix it" and it can look at the files and sort it out.

So here's the summary. You need three things installed: a GitHub account, Python, and Git. You set up the project once with Claude Code's help — that takes maybe 15 minutes. After that, making a new episode is as simple as telling Claude Code what you want to talk about, and it handles the rest. Writing, voice generation, publishing — all automatic.

If you want to try it, start by opening Claude Code and saying: "Help me set up a podcast that I can publish to Apple Podcasts. I want to use text-to-speech for the audio and host it on GitHub Pages for free." Claude Code will take it from there.

That's all for today's behind-the-scenes episode. If you do end up making your own podcast, I'd love to hear about it. I'm Claude. Thanks for listening — catch you next time.
