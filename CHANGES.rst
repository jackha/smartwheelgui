22/8
----

- now python 3.4 compatible 

- threads with semaphores for read and write

- SerialObject is renamed to SmartModule

- added first MockSerial

- cleanup

- use list_ports from serial package


TODO:

- update GUI with read value

- MockSerial behaves like a smart module

- real SmartModule?

- user command from GUI to SmartModule.


19/8
----

Jouw vragen aan de hand van mijn mini opzet:
- PAGE is denk ik leuk om een experiment mee te doen of om een proof of concept mee te doen, maar de samenhang in een programma zou ik liever zelf doen. Als je mijn versie config.py bekijkt is hij vele malen kleiner, hij ziet er overzichtelijker uit en hij doet nagenoeg hetzelfde.
- Scheiding tussen GUI en functionele dingen: zie onder
- Comport configuratie: wat bedoel je precies met "de combinatie gaat fout"? Op zich zijn dit technische details die waarschijnlijk niet ingewikkeld zijn voor mij om uit te zoeken. Ik heb wel een bugje opgelost en de aangepaste versie heb ik meegestuurd.
- Timers: ik heb wel iets als een thread.Timer gevonden. Wat was de frequentie die jij gebruikte?

De opzet die ik heb gemaakt is nog vrij minimaal en bevat:
- Een gescheiden GUI en het logica gedeelte, namelijk gui.py en serial_object.py
- Nog geen dingen met threads, maar die kunnen in SerialObject opgenomen worden. De GUI kan hier dus ook los ontwikkeld worden.
- Nog geen timer
- Ook nog geen functionele dingen

Als je de files uitpakt in je huidige python map, dan zou hij moeten werken. De config.py maakt gebruik van jouw listports.py. Ik heb er nog geen dingen ingestopt om hem robuuster te maken (zoals try/except tkinter en Tkinter).

gui.py
De code van de interface zit hier in. In de main wordt een window aangemaakt. Er worden instanties aangemaakt van SerialObject objecten aan de hand van config files. De SerialObject instanties bevatten de logica en het sturen/lezen/... van een SmartWheel. SerialObject wordt hier geimporteerd en staat in een losse file, serial_object.py

config.py
eerste probeersel om jouw comportconfig.py na te maken mbv tkinter en ttk.

serial_object.py
binnen een SerialObject object worden er meer low level dingen gedaan. deze kan ik uitbreiden zodat commando's van en naar een seriele poort in aparte threads worden gedaan. het object is zeg maar binnen python datgene wat 1 SmartWheel representeert en moet straks alle functionaliteiten bevatten / doorgeven wat de SmartWheel kan.

- Initial setup