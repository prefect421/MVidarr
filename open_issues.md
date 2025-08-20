1. artist detail page not accurately reflecting statistics
2. Display artist metadata under artist informmation
3. artist detail bulk action Add to Playlist redirects to video page and does not add to playlist
4. artist detail bulk action Preview Selected Does not work, remove button
5. artist detail bulk action Update Status does not give option of what to update status too.
6. artist detail metadata management UPdate from IMVDB button giving: Search failed due to network error
7. Redesign artist details Setting page to compress Artist MEtadata down to one page instead of four tabs. there is too much redundancy and hard to find fields.
8. Artist Detail page - artist header "Discover Videos" and "Settings" buttons are not working. remove them.
9. videos page filter error: [Generic] filtering videos: ReferenceError: displaySearchResults is not defined
    applyVideoFilters http://192.168.1.150:5000/videos:1960
videos:1814:13
Applying video filters... videos:1925:13
[Generic] filtering videos: ReferenceError: displaySearchResults is not defined
    applyVideoFilters http://192.168.1.150:5000/videos:1960
10. Make buttons under Bulk Operations use same text variable that is is used for the download button.
11. CC still not showing in video player on video detail page.
12. Video Detail page error: GET
http://192.168.1.150:5000/api/videos/222/subtitles/ATARASHII GAKKO! - Change (Official Music Video).en-ja.vtt
NS_BINDING_ABORTED
13. Video Detail Page: XHRGET
http://192.168.1.150:5000/api/themes/cyber
[HTTP/1.1 404 NOT FOUND 31ms]

	
GET
	http://192.168.1.150:5000/api/themes/cyber
Status
404
NOT FOUND
VersionHTTP/1.1
Transferred609 B (207 B size)
Referrer Policystrict-origin-when-cross-origin
DNS ResolutionSystem

    	
    Connection
    	close
    Content-Length
    	207
    Content-Type
    	text/html; charset=utf-8
    Date
    	Wed, 20 Aug 2025 14:15:02 GMT
    Server
    	Werkzeug/3.1.3 Python/3.12.3
    Set-Cookie
    	session=eyJfcGVybWFuZW50Ijp0cnVlLCJhdXRoZW50aWNhdGVkIjp0cnVlLCJ1c2VybmFtZSI6ImFkbWluIn0.aKXYZg.r-rOZ121Upp7GMqhCxKQuWck-tY; Expires=Thu, 21 Aug 2025 14:15:02 GMT; HttpOnly; Path=/; SameSite=Lax
    Vary
    	Cookie
    	
    Accept
    	*/*
    Accept-Encoding
    	gzip, deflate
    Accept-Language
    	en-US,en;q=0.5
    Connection
    	keep-alive
    Cookie
    	session=eyJfcGVybWFuZW50Ijp0cnVlLCJhdXRoZW50aWNhdGVkIjp0cnVlLCJ1c2VybmFtZSI6ImFkbWluIn0.aKXYZg.r-rOZ121Upp7GMqhCxKQuWck-tY; mvidarr_session=.eJyrVoovSC3KTcxLzStRsiopKk3VUUosLckAcjOTE0tSU2CCRfk5qUpWSokpuZl5SjpKpcWpRXmJuQihWgDukBot.aKTzfA.7Z-CGUQNHFbRjE67adaELYZvM8A
    DNT
    	1
    Host
    	192.168.1.150:5000
    Priority
    	u=4
    Referer
    	http://192.168.1.150:5000/video/222
    Sec-GPC
    	1
    User-Agent
    	Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0
14. video card add to playlist modal is not listing the existing playlists.
15. video cards don't stop displaying the refreshing metadata message after click refresh metadata button: 	Refreshing metadata from IMVDb and extracting technical data...
This may take a moment for video analysis
16. GET
http://192.168.1.150:5000/favicon.ico
[HTTP/1.1 404 NOT FOUND 0ms]

17. Playlist detail page. Play All button should play the playlist, not the entire library.
18. mvtv page remove subtitles button under video player
19. mvtv page add cc controls to the video player itself.
20. mvtv page make the artist and song clickable to take you to the detail page of either the artist or video depending on what you click
21. mvtv page make it so that if you click on a song in the queue you start playing that song.
22. mvtv page - cinematic player add cc controls to player
23. mvtv page - cinematic player remove previous from video controls
24. settings page move from a tab organization system to a side panel for the different settings areas.
25. if last.fm was added then we need to be able to configure that connection on the services settings area.
26. Theme customizer export theme: Failed to export theme: JSON.parse: unexpected character at line 1 column 1 of the JSON data
27. All download attempts failed. Last error: [youtube] opRRax4ph3E: Downloading tv client config [youtube] opRRax4ph3E: Downloading tv player API JSON [youtube] opRRax4ph3E: Downloading ios player API JSON [youtube] opRRax4ph3E: Downloading m3u8 information ERROR: [youtube] opRRax4ph3E: Requested format is not available. Use --list-formats for a list of available formatswsa
