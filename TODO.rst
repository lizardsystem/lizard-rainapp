TODO
====

In management script:
    - lower warn level to debug.
    - first test for existence of value, then go to fews. So 24 hour values are
      not fetched every time
    - add other value for fewsconnection error (-2)
    - in hover, show the reason for the error (no data, or connection error)

If I select a 2 day period, there should be a herhalingstijd for 2 days.

Window can be outside selected period, one may feel betrayed by that. Discuss.

Look closely again to how summary row comes to life.

T < 1 never happens, probably because of the formula.

Have a legend per parameterkey, instead of one legend for all parameters

Have a slider to navigate to available coloring of shapes in the current
daterange, only of there's a fewsunblobbed full of rainappdata.

Investigate if map rendering would speed up if simpler shapes would be used.
