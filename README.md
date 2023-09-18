# Minijam Music Transfer Tools
Tools for reading and writing music files to MMC/SD cards in the proprietary Minijam format.

## Background
Back in the early years of the PDA, the handspring Visor had an expansion slot called the springboard. One such accessory that was made available, was an MP3 player module, complete with a headphone jack and two thin MMC slots. To copy music to these devices, you needed to use a proprietary windows software tool. You would place the Visor PDA in its dock, and then run the transfer app on both the PC and on the Visor. You could then copy music across to an inserted MMC card, at the incredible speed of 15kB/s. 

## This project
You might be thinking, why not just take the card out, and copy music that way? Well, the device did not support any common file-systems, but instead relied upon its own proprietary format, for which no documentation is available. The only version of the PC software I have (v1.13, thanks to [Sb139 for uploading it here](https://archive.org/details/mini-jam-iso)), does not even work correctly with the firmware on my Innojam device (v4.01), resulting in corrupted file transfers, and music files that will not play back. However, an [MMC disk image file was also shared with me of a Minijam MMC card](https://archive.org/details/mini-jam-mmc-img), and by dissecting this file in a hex-editor, I was gradually able to reverse engineer a significant portion of the proprietary disk format. Not completely, but enough to be able to create a tool to perform basic work with these files.

**This python tool can:**
- Detect a Minijam formatted MMC
- Copy all music off the card to a PC
- Correctly erase the card
- Copy new music to the card

This tools works directly with an MMC card in a card reader -- there is no need to use the Visor for file transfer, which makes the process significantly quicker!

For any questions about this tool or the minijam springboard card, feel free to contact me, at <myusername> at gmail.com.




## Minijam MMC File System
I hope to provide a very brief overview of what I uncovered about the Minijam file system.

1. The entire disk is broken up into 512 byte "sectors. Each sector is identified by its position as an "sector ID", as three bytes, expressing byte offset in multiples of 256 bytes. For example, the first sector is offset 0x0 and sector ID 0x00 0x00 0x00, while the second sector is byte offset 0x200 (512) and sector ID 0x00 0x00 0x02 (512 / 256 = 2).
2. The last 6 bytes of every sector contain the sector ID of the neighboring previous and next sectors. e.g. at sector 56 (0x00 0x00 0x38), the neighbouring sector IDs would be 0x00 0x00 0x36 and 0x00 0x00 0x40. Thus, the last 6 bytes of the sector are 0x00 0x00 0x38 0x00 0x00 0x40. The exeption to this is the first sector, which has the last 6 bytes 0x00, except for the last 3, which corresponds to the last empty sector ID on the disk. This means that each sector on the disk can only contain 506 bytes of other data.
3. Three types of sectors make up the disk:
   - Disk info sector (1 sector)
   - File index sectors (256 sectors), each sector describing details and metadata for one file.
   - Data sectors (remainder of disk), each sector containing a portion (506 bytes) of data from a file.

### Disk Sector
The first sector contains information about the disk, in the format:
1. 4 bytes: Disk header, value "MJAE" = 0x4d 0x4a 0x41 0x45
2. 4 bytes: Number of sectors in the "index" region, default value 260 = 0x00 0x00 0x01 0x04 (This is not confirmed, but an educated guess)
3. 32 bytes: Disk name, in ASCII, default value "My MMC" = 0x4d 0x79 0x20 0x4d 0x4d 0x43
4. 2 bytes: Number of files on the disk (0x00 0x00)
5. 4 bytes: Total capacity of the disk, in bytes (e.g. 64MB MMC card = 63472640 bytes = 0x03 0xc8 0x84 0x00)
6. 4 bytes: Free physical space on the disk in bytes (e.g. 17M = 17094198 bytes = 0x01 0x04 0xd6 0x36)
7. 4 bytes: Free capacity on the disk, using 506 bytes of capacity per 512 bytes of sectors (e.g 17094198 bytes physical free space / 512 physical bytes per sector * 506 capacity bytes per sector = 16893822 bytes capacity = 0x01 0x01 0xC7 0x7E)
8. Rest of sector is empty (0x00).

### Second sector
The second sector is empty (0x00).

### Index Sectors
Each index sector describes the name, size, and metadata of the files, as well as indicating which subsquent data sectors contain the data content of the file. The index sector structure is:
1. 4 bytes: Index sector header. This appears to indicate the file type and possibly version of the index sector. The exact function is not yet determined, but the recommended bytes are "0xb2 0x00 0x00 0x00".
2. 128 bytes: The name of the file in ASCII hex.
3. 4 bytes:  the sector number of the first data sector containing the file data. Note: this is *half* the sector ID value, so if you double this value, you will get the sector ID. Or, if you multiply the sector number by 512 bytes, you will get the byte offset of the data section.
4. 4 bytes: the sector number of the last data sector containing the file data.
5. 4 bytes: the size of the file in bytes.
6. 2 bytes: purpose not determined, usually 0x00 0x7d.
7. 108 bytes: empty (0x00).
8. 30 bytes: The title of the song in ASCII hex.
9. 30 bytes: The artist of the song in ASCII hex.
10. 34 bytes: The album of the song in ASCII hex.
11. Further TAG/ID3 fields are available, but the exact format has not been further explored.

### Data Sectors
The data sectors are raw 506 slices of each file.



 
