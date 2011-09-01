Changelog of lizard-rainapp
===================================================


0.3 (2011-09-01)
----------------

- Using django json util now.


0.2 (2011-09-01)
----------------

- #3184 Removed graph from popup, put barchart on top. 

- Changed location id's to location names

- Fixed collage screen error

- Added export button in popup and collagescreen

- Added (mm) to max in rainstats

- Fixed bug in max calculation that neglected first value

- Adjusted max calculation that now only uses data that fully fit in the
  window


0.1 (2011-08-30)
----------------

- Added 'home screen' template. It points to jdbc sources as rainapp urls.

- Created and switched to specialized graph in nens-graph library that has
  with better legend positioning.

- Working rain statistics table.

- Added method to draw bar graphs. Added RainGraph to place the legend
  below the graph. [Alex]

- Initial library skeleton created by nensskel.  [Jack]
