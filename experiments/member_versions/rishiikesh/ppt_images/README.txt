ppt_images/  -- upload this whole folder to Overleaf
=====================================================

The 4 GRAPHS are already here. You must add the 4 PHOTOS yourself
(they were pasted into chat, not saved as files anywhere on this machine).

ALREADY IN THIS FOLDER
----------------------
  graph_walk.png        Amrith, walk, Room A      (CSI amplitude panel)
  graph_stand.png       Rishiikesh, stand, Room A
  graph_sit.png         Rishiikesh, sit, Room A
  graph_mixed.png       Gowreesh, mixed, Room B

  *_full.png            same 4, but with the sample-rate panel included.
                        Not used by the slides. Swap them in if you want
                        the rate plot shown too (they will render smaller).

YOU MUST ADD -- exact filenames, they are hardcoded in the slides
-----------------------------------------------------------------
  person_walk.jpg       the man mid-stride, walking
  person_stand.jpg      the man standing straight, arms at his sides
  person_sit.jpg        the man seated on the blue chair
  person_mixed.jpg      the two-person shot (one at the laptop/USRP,
                        one near the wall with hand raised)

  .jpg is what the slides expect. If yours are .png, either rename them
  or change the extension inside slides_13_14.tex.

HOW TO ADD THEM
---------------
  Save the 4 images from the chat with exactly those names into this
  folder, then upload the folder to Overleaf.

PATHS
-----
The slides reference   ppt_images/graph_walk.png   etc.
If Overleaf ends up putting the images in the project ROOT instead of
inside a ppt_images folder, delete the "ppt_images/" prefix from every
\includegraphics line in slides_13_14.tex.

WHERE THE SLIDES GO
-------------------
Paste the contents of slides_13_14.tex into your .tex file immediately
after the frame titled "12. Optimal Subcarrier Selection per Activity".
