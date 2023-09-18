# Minijam Music Transfer Tools
Tools for reading and writing music files to MMC/SD cards in the proprietary Minijam format.

## Background
Back in the early years of the PDA, the handspring Visor had an expansion slot called the springboard. One such accessory that was made available, was an MP3 player module, complete with a headphone jack and two thin MMC slots. To copy music to these devices, you needed to use a proprietary windows software tool. You would place the Visor PDA in its dock, and then run the transfer app on both the PC and on the Visor. You could then copy music across to an inserted MMC card, at the incredible speed of 15kB/s. 

## This project
You might be thinking, why not just take the card out, and copy music that way? Well, the device did not support any common file-systems, but instead relied upon its own proprietary format, for which no documentation is available. The only version of the PC software I have (v1.13), does not even work correctly with the firmware on my Innojam device (v4.01), resulting in corrupted file transfers, and music files that will not play back. However, a disk image file was shared with me of a Minijam MMC card, and by dissecting this file in a hex-editor, I was gradually able to reverse engineer a significant portion of the proprietary disk format. Not completely, but enough to be able to create two tools:

1. A tool to read a Minijam formatted MMC, and copy all music off the card to a PC
2. A tool to detect an inserted Minijam formatted MMC, that can then re-format the card, and optionally copy music from a folder on the PC to the card.

Both of these tools work directly with an MMC card in a card reader, there is no need to use the Visor for file transfer, which makes the process significantly quicker!

For any questions about this tool or the minijam springboard card, feel free to contact me, at <myusername> at gmail.com.

