# TetraDecaPost
There are a few issues with the Siemens NX post processor infrastructure. Namely, it's:
* Slow. 100KiB/s throughput for 3 gigabyte toolpaths is bullshit. I have deadlines to hit and a life to live. It can't take weeks to post process a toolpath. That's just not acceptable. Not now, not ever, not anywhere, not by any stretch.
* Implemented in TCL. Seriously, what the fuck? I would laugh, but this is no joke.
* Massively complex. Inevitably, because it's interpreted scripting shit that has been added to by thousands of people for decades.
* Difficult to modify, understand, or debug.
* Extremely offensively nickel-and-dime commercialized. If you buy a ready-made post, it will be encrypted and locked to a single license. This is less than worthless to me. It has immense negative value. I need to understand what my post is doing. Most machinists aren't coders, but I am, so fuck you.

So, I'm reimplementing those parts useful to me as I see fit, and nobody can do a God damned thing to stop me. Also, I'm publishing all the code so that anybody can do anything they want with it. With ANGER.
