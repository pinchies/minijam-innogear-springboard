# finds an inserted minijam-formatted MMC card
# and replaces the contents with the songs found in the ./songs folder

import os
import sys
import time
import wmi
import struct
import math
# id3 tag reading
import eyed3
eyed3.log.setLevel("ERROR")

# block size in bytes
BLOCK_SIZE = 512
print("=== Minijam tool v1.0 by pinchies ===\n", flush=True)
print("For any questions about this tool or the minijam springboard card, feel free to contact me, at <mygithubusername> at gmail.com. I imagine that less than 10 people on the planet would ever use this tool, so if you do find it useful, please do let me know! :-)\n", flush=True)
# wait 3 seconds
time.sleep(3)

print("Scanning for drives...", end="", flush=True)
found = 0
w=wmi.WMI()
w.Win32_DiskDrive()
for drive in w.Win32_DiskDrive():
    for partition in drive.associators ("Win32_DiskDriveToDiskPartition"):
        for logical_disk in partition.associators ("Win32_LogicalDiskToPartition"):
            if logical_disk.Filesystem == None:
                # try and read the first sector of the drive and see if it's a minijam card
                volume = open('\\\\.\\%s' % logical_disk.DeviceID, 'rb+')
                volume.seek(0)
                sector = volume.read(BLOCK_SIZE)
                volumeformat = sector[:4].decode('ascii', errors='ignore')
                # check first 4 bytes of sector as ascii
                if volumeformat == 'MJAE':
                    print('Minijam card detected.')
                    found = 1
                    
if found == 0:
    print("No minijam card detected in the PC! Please format the MMC card in the module, using the minijam 'MiniLoader' app on the Visor first, and then try run this tool again.")
    sys.exit(0)

# print capacity of disk image
drivecapacity = int(drive.Size)
sectorcount = int(drivecapacity / BLOCK_SIZE)
print("Drive capacity: " + str(int(drivecapacity/1000/1000)) + " MB (" + str(sectorcount) + " sectors)")

formatcard = 0
quickformat = 0
writing = 3

# ask the user if they want to download the songs from the card
downloadsongs = 0
downloadsongsinput = input("Download songs from card? (y/n): ")
if downloadsongsinput == "y":
    downloadsongs = 1

# download songs from card
if downloadsongs == 1:
    # read first sector
    volume.seek(0)
    initsector = volume.read(BLOCK_SIZE)
    initsector = bytearray(initsector)
    # get file count
    songcount = int.from_bytes(initsector[40:42], byteorder='big')
    print("Found " + str(songcount) + " songs on card.")
    # read each file
    for i in range(0, songcount):
        # read file index sector
        indexsector = i + 2
        volume.seek(indexsector * BLOCK_SIZE)
        songsector = volume.read(BLOCK_SIZE)
        songsector = bytearray(songsector)
        # print("Reading song sector " + str(indexsector))
        # print("sector as hex: " + str(songsector.hex()))
        
        # get song filename
        songfilename = songsector[4:132].decode('ascii', errors='ignore')
        # trim trailing 0s
        songfilename = songfilename.split('\x00')[0]
        print("Downloading song: " + str(songfilename) + " ...", end="", flush=True)

        # get song data offset address
        songdataoffset = int.from_bytes(songsector[132:136], byteorder='big')
        # get song data size
        songdatasize = int.from_bytes(songsector[140:144], byteorder='big')
        # get song data end address
        songdataend = int.from_bytes(songsector[136:140], byteorder='big')
        
        # read song data
        songdata = bytearray()
        for j in range(0, math.ceil(songdatasize / (BLOCK_SIZE-6))):
            # read current data sector
            currentdatasectoroffset = songdataoffset*BLOCK_SIZE + j*BLOCK_SIZE
            volume.seek(int(currentdatasectoroffset))
            songdatasector = volume.read(BLOCK_SIZE)
            songdatasector = bytearray(songdatasector)
            songdata = songdata + songdatasector[0:BLOCK_SIZE-6]

        # check if downloaded folder exists
        if not os.path.exists("downloaded"):
            os.makedirs("downloaded")


        # append .mp3 to filename if it doesn't already exist
        if songfilename[-4:] != ".mp3":
            songfilename = songfilename + ".mp3"

        # write song data to file
        songfile = open("downloaded/" + songfilename, 'wb')
        songfile.write(songdata)
        songfile.close()
       
        print("Done.")





# ask the user if they want to format the card
formatcardinput = input("Format card? (y/n): ")
if formatcardinput == "y":
    formatcard = 1
    # ask the user if they want to quick format the card
    quickformatinput = input("Quick format? (y/n): ")
    if quickformatinput == "y":
        quickformat = 1


if formatcard == 1:
    print("Formatting card...", end="", flush=True)
    # format the card sectors
    for i in range(0, sectorcount):
        sectoroffset = 2*i
        volume.seek(i * BLOCK_SIZE)
        # init sector data with 0s
        sector = bytearray(BLOCK_SIZE)


        if sectoroffset != 0:
            # set last 6 bytes of sector to offsets of neighboring sectors as 3 byte hex
            prevsectoroffset = sectoroffset - 2
            nextsectoroffset = sectoroffset + 2
            prevsectoroffsetbytes = prevsectoroffset.to_bytes(3, byteorder='big')
            nextsectoroffsetbytes = nextsectoroffset.to_bytes(3, byteorder='big')
            sector[-6:-3] = prevsectoroffsetbytes
            sector[-3:] = nextsectoroffsetbytes
        else:
            # first sector is different
            startbytes = "4d 4a 41 45 00 00 01 04 4d 79 20 4d 4d 43" # Card Format Indicator: "MJAE" + 260 + Volume name: "My MMC" -- maybe 260 is length of index region in kB?
            sector[0:14] = bytearray.fromhex(startbytes)
            trackcountbytes = "00 00"
            volumesizebytes = drivecapacity.to_bytes(4, byteorder='big')
            songdatacapacity = drivecapacity - 259578 # drive space less the size of the init sector and the index sector?
            volumefreebytes = (songdatacapacity).to_bytes(4, byteorder='big')
            volumefreebytes2 = (songdatacapacity - 506).to_bytes(4, byteorder='big')
            sector[40:42] = bytearray.fromhex(trackcountbytes)
            sector[42:46] = volumesizebytes
            sector[46:50] = volumefreebytes 
            sector[50:54] = volumefreebytes2

            lastfreesectoroffsetbytes = "00 04 02"
            prevsectoroffset = 0
            nextsectoroffset = bytearray.fromhex(lastfreesectoroffsetbytes)
            sector[-3:] = nextsectoroffset
        if i>0 and i % int(sectorcount/100) == 0:
            print(".", end="", flush=True)
            writing = writing - 1
        
        if quickformat and writing <= 0:
            break
        # read old sector
        volume.seek(i * BLOCK_SIZE)
        oldsector = volume.read(BLOCK_SIZE)
        oldsector = bytearray(oldsector)
        # compare old sector to new sector
        same = 1
        for j in range(0, BLOCK_SIZE):
            #print("comparing byte " + str(j))
            if oldsector[j] != sector[j]:
                # print("#", end="", flush=True)
                #print("sector " + str(i) + " is different at byte " + str(j))
                #print("old byte hex: " + str(oldsector[j]))
                #print("new byte hex: " + str(sector[j]))
                writing = 3
                same = 0
                break
        if same == 0:
            # write new sector
            volume.seek(i * BLOCK_SIZE)
            writebytes = volume.write(sector)
            # print("wrote " + str(writebytes) + " bytes to sector " + str(i))
            # print("old sector as hex: " + str(oldsector.hex()))
            # print("new sector as hex:     " + str(sector.hex()))
    print("Done.")

# ask the user if they want to write songs to the card
writesongs = 0
writesongsinput = input("Write songs (mp3 files from ./songs folder)  to card? (y/n): ")
if writesongsinput == "y":
    writesongs = 1

 # write songs to card
if writesongs == 1:
    # read first sector
    volume.seek(0)
    initsector = volume.read(BLOCK_SIZE)
    initsector = bytearray(initsector)
  
    # get list of mp3 files in songs folder
    songlist = os.listdir("songs")
    addsongcount = len(songlist)
    print("Found " + str(addsongcount) + " songs to add.")
    
    # write each song in list to card
    for i in range(0, addsongcount):

        # find next free index sector
        oldsongcount = int.from_bytes(initsector[40:42], byteorder='big')
        indexsector = oldsongcount + 2
        #print("next free index sector: " + str(indexsector))
        volume.seek(indexsector * BLOCK_SIZE)
        oldsongsector = volume.read(BLOCK_SIZE)

        # read old song index sector
        songsector = oldsongsector
        songsector = bytearray(songsector)

        # set file format/type/version -- possibly determines which metadata fields are used?
        songsector[0:4] = bytearray.fromhex("b2 00 00 00")
    
        # get song filename
        songfilename = songlist[i]
        print("Adding song: " + str(songfilename))

        # get song data
        songdata = open("songs/" + songfilename, 'rb')
        songbytes = songdata.read()

        # ascii encode song name, remove file extension, trim to 128 bytes, and pad with 0s 
        songfilenamebytes = bytearray(songfilename[:-4], 'ascii',errors='ignore')
        songfilenamebytes = songfilenamebytes[:128]
        songfilenamebytes = songfilenamebytes + bytearray(128-len(songfilenamebytes))
        # write song filename to sector
        songsector[4:132] = songfilenamebytes

        # get song id3 tag
        songdata = eyed3.load("songs/" + songfilename)
        if songdata.tag == None:
            songdata.initTag()
    
        # get song title from id3 tag
        if songdata.tag.title == None:
            songdata.tag.title = songfilename
        songtitle = songdata.tag.title
        # ascii encode song track title
        songtitlebytes = bytearray(songtitle, 'ascii',errors='ignore')
        # trim to 30 bytes and pad with 0s
        songtitlebytes = songtitlebytes[:30]
        songtitlebytes = songtitlebytes + bytearray(30-len(songtitlebytes))
        # write song title to sector
        songsector[254:284] = songtitlebytes

        # get song artist from id3 tag
        if songdata.tag.artist == None:
            songdata.tag.artist = " "
        songartist = songdata.tag.artist
        # ascii encode song artist
        songartistbytes = bytearray(songartist, 'ascii',errors='ignore')
        # trim to 30 bytes and pad with 0s
        songartistbytes = songartistbytes[:30]
        songartistbytes = songartistbytes + bytearray(30-len(songartistbytes))
        # write song artist to sector
        songsector[284:314] = songartistbytes

        # get song album from id3 tag
        if songdata.tag.album == None:
            songdata.tag.album = " "
        songalbum = songdata.tag.album
        # ascii encode song album
        songalbumbytes = bytearray(songalbum, 'ascii',errors='ignore')
        # trim to 30 bytes and pad with 0s
        songalbumbytes = songalbumbytes[:34]
        songalbumbytes = songalbumbytes + bytearray(34-len(songalbumbytes))
        # write song album to sector
        songsector[314:348] = songalbumbytes
        
        # # get song year from id3 tag
        # if songdata.tag.year == None:
        #     songdata.tag.year = " "
        # songyear = songdata.tag.year
        # # ascii encode song year
        # songyearbytes = bytearray(songyear, 'ascii',errors='ignore')

        # # get song genre from id3 tag
        # if songdata.tag.genre == None:
        #     songdata.tag.genre = " "
        # songgenre = songdata.tag.genre
        # # ascii encode song genre
        # songgenrebytes = bytearray(songgenre, 'ascii',errors='ignore')

        # # get song track number from id3 tag
        # if songdata.tag.track_num == None:
        #     songdata.tag.track_num = " "
        # songtracknumber = songdata.tag.track_num
        # # ascii encode song track number
        # songtracknumberbytes = bytearray(songtracknumber, 'ascii',errors='ignore')

        # # get song comment from id3 tag
        # if songdata.tag.comments == None:
        #     songdata.tag.comments = " "
        # songcomment = songdata.tag.comments
        # # ascii encode song comment
        # songcommentbytes = bytearray(songcomment, 'ascii',errors='ignore')

        # # get song length from id3 tag
        # songlength = songdata.info.time_secs
        # # ascii encode song length
        # songlengthbytes = bytearray(songlength, 'ascii',errors='ignore')

        # # get song bitrate from id3 tag
        # songbitrate = songdata.info.bit_rate_str
        # # ascii encode song bitrate
        # songbitratebytes = bytearray(songbitrate, 'ascii',errors='ignore')

        # # get song sample rate from id3 tag
        # songsamplerate = songdata.info.sample_rate_str
        # # ascii encode song sample rate
        # songsampleratebytes = bytearray(songsamplerate, 'ascii',errors='ignore')

        # # get song channel count from id3 tag
        # songchannelcount = songdata.info.mode
        # # ascii encode song channel count
        # songchannelcountbytes = bytearray(songchannelcount, 'ascii',errors='ignore')

        # # get song file format from id3 tag
        # songfileformat = songdata.info.mime_type
        # # ascii encode song file format
        # songfileformatbytes = bytearray(songfileformat, 'ascii',errors='ignore')

        # get song file size
        songsize = os.path.getsize("songs/" + songfilename)
        #print("song size: " + str(songsize) + " bytes = " + str(songsize.to_bytes(4, byteorder='big')))
    
        # get data start sector from next free index sector
        nextfreesectoroffset = initsector[-3:]
        datastartoffset = int(int.from_bytes(nextfreesectoroffset, byteorder='big')/2*BLOCK_SIZE)
        #print("next free sector offset: " + str(nextfreesectoroffset))
        #print("data start offset: " + str(datastartoffset) + " bytes = " + str(datastartoffset.to_bytes(4, byteorder='big')))
        dataendoffset = datastartoffset + (math.ceil(songsize / (BLOCK_SIZE-6))-1)*BLOCK_SIZE # -1 because first data sector is already allocated
        #print("data end offset: " + str(dataendoffset) + " bytes = " + str(dataendoffset.to_bytes(4, byteorder='big')))
        nextfreesectoroffset = (datastartoffset + (math.ceil(songsize / (BLOCK_SIZE-6))+1)*BLOCK_SIZE)*2/BLOCK_SIZE

        # get volume free space from init sector
        volumefreespace = int.from_bytes(initsector[46:50], byteorder='big')
        #print("volume free space: " + str(volumefreespace) + " bytes = " + str(volumefreespace.to_bytes(4, byteorder='big')))

        # calculate required free space for song
        requiredfreespace = math.ceil(songsize/506)*512

        # check if song will fit on card
        if requiredfreespace > volumefreespace:
            print("Card full! Song " + str(songfilename) + " will not fit on card")
            break

        # update initsector: increment song count, update volume free space 1 and 2, and update next free sector offset
        initsector[40:42] = int(oldsongcount + 1).to_bytes(2, byteorder='big')
        initsector[46:50] = int(volumefreespace - requiredfreespace).to_bytes(4, byteorder='big')
        initsector[50:54] = int(volumefreespace - requiredfreespace - 506).to_bytes(4, byteorder='big')
        initsector[-3:] = int(nextfreesectoroffset).to_bytes(3, byteorder='big')
        
        # write new initsector
        volume.seek(0)
        writebytes = volume.write(initsector)
        #print("wrote " + str(len(initsector)) + " bytes to initsector")
        #print("wrote hex: " + str(initsector.hex()))

        # prepare song data offset address
        songsector[132:136] = int(datastartoffset/BLOCK_SIZE).to_bytes(4, byteorder='big')
        songsector[136:140] = int(dataendoffset/BLOCK_SIZE).to_bytes(4, byteorder='big')
       
        # prepare song data size
        songsector[140:144] = int(songsize).to_bytes(4, byteorder='big')
                        
        # write song metadata index sector
        volume.seek(indexsector * BLOCK_SIZE)
        writebytes = volume.write(songsector)
        #print("wrote " + str(len(songsector)) + " bytes to song sector " + str(indexsector))
        #print("wrote hex: " + str(songsector.hex()))

        # write song data to data sector
        for j in range(0, math.ceil(songsize / (BLOCK_SIZE-6))):
            # read current data sector
            #     print("data sector ID " + str(int(datastartoffset/BLOCK_SIZE)+j*2))
            #     print("offset " + str(datastartoffset + j*BLOCK_SIZE))
            currentdatasectoroffset = datastartoffset + j*BLOCK_SIZE
            #print("reading offset " + str(currentdatasectoroffset))
            volume.seek(int(currentdatasectoroffset))
            songdatasector = volume.read(BLOCK_SIZE)
            songdatasector = bytearray(songdatasector)
            songdataforsector = songbytes[j*(BLOCK_SIZE-6):(j+1)*(BLOCK_SIZE-6)]
            
            # if songdataforsector is less than 506 bytes, pad with 0s
            if len(songdataforsector) < 506:
                songdataforsector = songdataforsector + bytearray(506-len(songdataforsector))
            songdatasector[0:BLOCK_SIZE-6] = songdataforsector
            
            # write song data to sector
            volume.seek(int(currentdatasectoroffset))
            writebytes = volume.write(songdatasector)

            #print("wrote " + str(writebytes) + " bytes to song data sector " + str(int(currentdatasectoroffset/BLOCK_SIZE)+j*2) + " at offset " + str(currentdatasectoroffset))
            #print("wrote hex: " + str(songdatasector.hex()))