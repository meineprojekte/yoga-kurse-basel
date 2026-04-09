#!/usr/bin/env python3
"""
Generate SEO landing pages for yoga style + city combinations.
Creates pages at /yoga/{style}-{city}/index.html for the top 10 styles
in the top 6 Swiss cities, but only if actual studios offer that style.
"""

import json
import os
import re
import html
from collections import defaultdict
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "yoga")
BASE_URL = "https://meineprojekte.github.io/yoga-kurse-basel"

# --- City definitions: city_name, canton_id, file_key, url_slug ---
CITIES = [
    {"name": "Zürich",   "canton_id": "zurich",      "file_key": "zurich",      "url_slug": "zuerich"},
    {"name": "Basel",    "canton_id": "basel-stadt",  "file_key": "basel",        "url_slug": "basel"},
    {"name": "Bern",     "canton_id": "bern",         "file_key": "bern",         "url_slug": "bern"},
    {"name": "Luzern",   "canton_id": "luzern",       "file_key": "luzern",       "url_slug": "luzern"},
    {"name": "Genf",     "canton_id": "geneve",       "file_key": "geneve",       "url_slug": "genf"},
    {"name": "Lausanne", "canton_id": "vaud",         "file_key": "vaud",         "url_slug": "lausanne"},
]

# --- Style definitions ---
STYLES = [
    {
        "name": "Vinyasa",
        "url_slug": "vinyasa-yoga",
        "display": "Vinyasa Yoga",
        "match_terms": ["vinyasa", "vinyasa flow", "creative vinyasa", "hot vinyasa", "dynamic flow", "power flow", "energy flow"],
        "description_key": "vinyasa",
    },
    {
        "name": "Hatha",
        "url_slug": "hatha-yoga",
        "display": "Hatha Yoga",
        "match_terms": ["hatha", "hatha flow", "hatha raja", "tantra hatha", "alignment hatha"],
        "description_key": "hatha",
    },
    {
        "name": "Yin",
        "url_slug": "yin-yoga",
        "display": "Yin Yoga",
        "match_terms": ["yin", "yin yoga"],
        "description_key": "yin",
    },
    {
        "name": "Ashtanga",
        "url_slug": "ashtanga-yoga",
        "display": "Ashtanga Yoga",
        "match_terms": ["ashtanga", "ashtanga mysore", "ashtanga led", "ashtanga-vinyasa", "ashtanga-inspired", "mysore"],
        "description_key": "ashtanga",
    },
    {
        "name": "Hot Yoga / Bikram",
        "url_slug": "hot-yoga",
        "display": "Hot Yoga / Bikram",
        "match_terms": ["bikram", "bikram yoga", "bikram hot yoga", "hot yoga", "hot vinyasa", "hot let it flow", "inferno hot pilates"],
        "description_key": "hot",
    },
    {
        "name": "Kundalini",
        "url_slug": "kundalini-yoga",
        "display": "Kundalini Yoga",
        "match_terms": ["kundalini"],
        "description_key": "kundalini",
    },
    {
        "name": "Power Yoga",
        "url_slug": "power-yoga",
        "display": "Power Yoga",
        "match_terms": ["power yoga", "power", "power flow"],
        "description_key": "power",
    },
    {
        "name": "Aerial Yoga",
        "url_slug": "aerial-yoga",
        "display": "Aerial Yoga",
        "match_terms": ["aerial", "aerial yoga"],
        "description_key": "aerial",
    },
    {
        "name": "Schwangerschaftsyoga",
        "url_slug": "schwangerschaftsyoga",
        "display": "Schwangerschaftsyoga",
        "match_terms": ["prenatal", "schwangerschaftsyoga", "prenatal yoga"],
        "description_key": "prenatal",
    },
    {
        "name": "Restorative Yoga",
        "url_slug": "restorative-yoga",
        "display": "Restorative Yoga",
        "match_terms": ["restorative", "restorative flow", "restorative yoga"],
        "description_key": "restorative",
    },
]

# --- Unique descriptions per style (in German) ---
STYLE_DESCRIPTIONS = {
    "vinyasa": {
        "what": "Vinyasa Yoga ist ein dynamischer, fliessender Yogastil, bei dem Bewegung und Atem synchronisiert werden. Jede Klasse ist anders aufgebaut — die Sequenzen variieren und führen die Übenden durch kreative Übergänge von einer Pose zur nächsten. Der Name \"Vinyasa\" bedeutet \"Bewegung im Einklang mit dem Atem\".",
        "why_city": {
            "zuerich": "In Zürich ist Vinyasa Yoga der beliebteste Yogastil. Die dynamische, kosmopolitische Stadt zieht Menschen an, die einen aktiven Lebensstil pflegen und im Flow ihre Balance finden. Dutzende Studios in der ganzen Stadt bieten Vinyasa-Klassen an — vom Kreis 4 bis zum Seefeld.",
            "basel": "Basel hat eine lebendige Vinyasa-Szene mit zahlreichen Studios, die kreative Flow-Klassen anbieten. Die Kulturstadt am Rhein verbindet urbanes Flair mit einer bewussten Lebensweise, was Vinyasa Yoga hier besonders beliebt macht.",
            "bern": "In der Bundesstadt Bern finden Vinyasa-Liebhaber ein vielfältiges Angebot. Die entspannte Atmosphäre der UNESCO-Welterbe-Stadt bietet den perfekten Kontrast zur dynamischen Praxis auf der Matte.",
            "luzern": "Luzern verbindet die Dynamik des Vinyasa Yoga mit der inspirierenden Kulisse von See und Bergen. Die Studios der Leuchtenstadt bieten Vinyasa-Klassen für alle Levels an.",
            "genf": "In der internationalen Stadt Genf ist Vinyasa Yoga besonders bei der kosmopolitischen Bevölkerung beliebt. Viele Studios bieten Kurse auf Französisch und Englisch an.",
            "lausanne": "Lausanne am Genfersee ist ein Zentrum für sportliche Aktivitäten, und Vinyasa Yoga passt perfekt zur aktiven Lebensweise der olympischen Hauptstadt.",
        },
        "who": "Vinyasa Yoga eignet sich für alle, die eine aktive, abwechslungsreiche Praxis suchen. Anfänger sind in den meisten Klassen willkommen — achte auf die Level-Angabe. Besonders beliebt bei sportlichen Menschen, die Kraft, Flexibilität und Meditation verbinden möchten.",
        "expect": "In einer typischen Vinyasa-Klasse (60-75 Minuten) beginnst du mit Atemübungen und Aufwärmung. Dann folgen fliessende Sequenzen, die an Intensität zunehmen. Die Stunde schliesst mit Dehnungen und einer Entspannung in Savasana. Jeder Lehrer bringt seinen eigenen Stil ein — keine zwei Klassen sind gleich.",
    },
    "hatha": {
        "what": "Hatha Yoga ist der Ursprung aller körperlichen Yogastile und bildet die Grundlage für die meisten modernen Yogarichtungen. Die Praxis umfasst Körperhaltungen (Asanas), Atemübungen (Pranayama) und Meditation. Hatha bedeutet \"Kraft\" und steht für die Verbindung von Sonne (Ha) und Mond (Tha) — Aktivität und Ruhe in Balance.",
        "why_city": {
            "zuerich": "In Zürich hat Hatha Yoga eine lange Tradition. Viele der ältesten und etabliertesten Studios der Stadt haben Hatha als Grundlage ihres Angebots. Wer die Basis des Yoga verstehen möchte, findet hier erfahrene Lehrer mit jahrzehntelanger Praxis.",
            "basel": "Basels Yoga-Szene hat starke Hatha-Wurzeln. Das älteste Yoga-Zentrum der Stadt, gegründet 1994, bietet seit drei Jahrzehnten traditionelles Hatha Yoga an. Die ruhige, gründliche Herangehensweise passt zur Basler Mentalität.",
            "bern": "In Bern wird Hatha Yoga besonders geschätzt — die Bundesstadt bevorzugt das Bewährte. Zahlreiche Studios bieten klassisches Hatha für alle Altersgruppen an, von Studenten bis Senioren.",
            "luzern": "Luzern mit seinem ruhigen Charme ist wie geschaffen für Hatha Yoga. Die Studios am See legen Wert auf Präzision und Achtsamkeit in jeder Pose.",
            "genf": "Hatha Yoga hat in Genf eine treue Anhängerschaft. Die traditionelle Praxis bietet einen ruhigen Gegenpol zum hektischen internationalen Alltag der Stadt.",
            "lausanne": "In Lausanne verbinden viele Studios Hatha Yoga mit modernen Ansätzen. Die Stadt bietet eine gute Mischung aus traditionellen und zeitgenössischen Hatha-Klassen.",
        },
        "who": "Hatha Yoga ist ideal für Einsteiger, da die Posen einzeln erklärt und länger gehalten werden. Aber auch erfahrene Yogis kommen auf ihre Kosten — fortgeschrittene Hatha-Klassen können sehr anspruchsvoll sein. Perfekt für alle, die eine ruhige, gründliche Praxis bevorzugen.",
        "expect": "Eine Hatha-Klasse dauert meist 60-90 Minuten. Du hältst Asanas für mehrere Atemzüge, was dir Zeit gibt, die Ausrichtung zu spüren und zu verfeinern. Zwischen den Posen gibt es Pausen. Pranayama (Atemübungen) und eine abschliessende Meditation oder Tiefenentspannung gehören fast immer dazu.",
    },
    "yin": {
        "what": "Yin Yoga ist ein ruhiger, meditativer Yogastil, bei dem Posen drei bis fünf Minuten oder länger gehalten werden. Dabei werden tiefe Bindegewebsschichten (Faszien), Bänder und Gelenke angesprochen, die bei aktiveren Yogastilen kaum erreicht werden. Die Praxis basiert auf Prinzipien der traditionellen chinesischen Medizin und arbeitet mit den Meridianen des Körpers.",
        "why_city": {
            "zuerich": "In der schnelllebigen Zürcher Geschäftswelt ist Yin Yoga der perfekte Ausgleich. Immer mehr Berufstätige entdecken die tiefe Entspannung, die diese Praxis bietet. Zahlreiche Studios in Zürich haben Yin-Klassen fest im Programm.",
            "basel": "Basel mit seiner Pharma- und Kulturszene weiss um die Bedeutung von Regeneration. Yin Yoga wird in vielen Basler Studios als Ergänzung zu dynamischeren Stilen angeboten und ist besonders am Abend beliebt.",
            "bern": "In Bern hat Yin Yoga eine wachsende Fangemeinde. Die meditative Praxis harmoniert mit der ruhigen Atmosphäre der Bundesstadt und bietet gestressten Beamten und Politikern einen willkommenen Ausgleich.",
            "luzern": "Die ruhige Atmosphäre Luzerns am Vierwaldstättersee ist wie geschaffen für Yin Yoga. Studios nutzen die natürliche Gelassenheit der Stadt als Rahmen für tiefe, meditative Praxis.",
            "genf": "Im internationalen Genf suchen viele Menschen nach Wegen, Stress abzubauen. Yin Yoga bietet genau das — und wird in der Rhonestadt immer beliebter.",
            "lausanne": "Lausanne bietet eine wachsende Auswahl an Yin-Yoga-Klassen, die den perfekten Ausgleich zum aktiven Lebensstil am Genfersee bilden.",
        },
        "who": "Yin Yoga ist für alle geeignet — vom kompletten Anfänger bis zum erfahrenen Yogi. Es ist besonders empfehlenswert für Menschen mit viel Stress, für Sportler zur Regeneration und für alle, die ihre Flexibilität sanft verbessern möchten. Keine Vorkenntnisse nötig.",
        "expect": "In einer Yin-Klasse (60-75 Minuten) nimmst du hauptsächlich sitzende oder liegende Positionen ein, die 3-5 Minuten gehalten werden. Hilfsmittel wie Bolster, Blöcke und Decken unterstützen dich. Die Stunde ist ruhig, oft mit sanfter Musik oder in Stille. Erwarte keine Schweissausbrüche — aber tiefe innere Arbeit.",
    },
    "ashtanga": {
        "what": "Ashtanga Yoga ist ein kraftvoller, strukturierter Yogastil, der auf dem Lehrsystem von Sri K. Pattabhi Jois basiert. Es gibt sechs festgelegte Serien von Asanas, die immer in derselben Reihenfolge praktiziert werden. Die Praxis verbindet Atem (Ujjayi), Blickpunkte (Drishti) und Energieverschlüsse (Bandhas) zu einem intensiven, meditativen Erlebnis.",
        "why_city": {
            "zuerich": "Zürich hat eine starke Ashtanga-Community mit mehreren dedizierten Shalas. Autorisierte Lehrer bieten tägliche Mysore-Klassen an, und die Stadt zieht regelmässig internationale Ashtanga-Lehrer für Workshops an.",
            "basel": "In Basel gibt es eine leidenschaftliche Ashtanga-Szene mit spezialisierten Studios, die tägliche Mysore-Praxis und geführte Klassen anbieten. Die Basler Ashtanga-Community ist eng vernetzt und unterstützend.",
            "bern": "Berns Ashtanga-Praktizierende schätzen die Disziplin und Regelmässigkeit dieser Tradition. Mehrere Studios bieten die traditionelle Mysore-Methode an, bei der jeder Schüler individuell betreut wird.",
            "luzern": "Auch in Luzern hat Ashtanga Yoga seinen Platz gefunden. Studios bieten sowohl Mysore- als auch geführte Klassen an, eingebettet in die inspirierende Bergkulisse.",
            "genf": "Genfs internationale Community hat eine starke Affinität zum Ashtanga Yoga. Die strukturierte Praxis spricht besonders disziplinierte Übende an.",
            "lausanne": "In Lausanne wächst die Ashtanga-Gemeinschaft stetig. Die olympische Stadt schätzt die athletische Herausforderung dieser traditionellen Praxis.",
        },
        "who": "Ashtanga Yoga zieht disziplinierte, ausdauernde Praktizierende an. Anfänger sind in Mysore-Klassen willkommen — dort erhält jeder individuelle Anleitung. Geführte Klassen erfordern etwas Erfahrung. Ideal für alle, die eine klare Struktur und messbare Fortschritte schätzen.",
        "expect": "Mysore-Klassen finden früh morgens statt (oft 6:30-9:00). Du praktizierst selbstständig die erste Serie in deinem eigenen Tempo, während der Lehrer durch den Raum geht und Anpassungen gibt. Geführte Klassen (\"Led\") folgen dem Sanskrit-Zählen des Lehrers. Erwarte eine intensive, schweisstreibende Praxis.",
    },
    "hot": {
        "what": "Hot Yoga wird in einem auf 35-42°C beheizten Raum praktiziert. Die bekannteste Form ist Bikram Yoga mit einer festen Abfolge von 26 Posen und 2 Atemübungen in 90 Minuten. Moderne Hot-Yoga-Varianten bieten auch Vinyasa-Flows oder Hatha-Sequenzen bei erhöhter Temperatur. Die Wärme fördert Flexibilität, Entgiftung und intensives Schwitzen.",
        "why_city": {
            "zuerich": "Zürich war Pionier des Hot Yoga in der Schweiz — das erste Bikram-Studio des Landes wurde hier 2004 eröffnet. Heute gibt es mehrere Hot-Yoga-Optionen in der Stadt, von traditionellem Bikram bis zu Hot Vinyasa.",
            "basel": "Basel hat sein eigenes Bikram-Studio mit maximal 18 Teilnehmern pro Klasse — eine intensive, persönliche Erfahrung. Die Nachfrage nach Hot Yoga wächst auch in der Rheinstadt stetig.",
            "bern": "In Bern findet man Hot-Yoga-Angebote, die besonders in den kalten Wintermonaten beliebt sind. Die erhitzte Praxis bietet einen wärmenden Kontrast zum Berner Nebel.",
            "luzern": "Luzern bietet Hot-Yoga-Klassen für alle, die eine besonders intensive Praxis suchen. Die Kombination aus Hitze und Yoga spricht sportliche Menschen in der Zentralschweiz an.",
            "genf": "In Genf erfreut sich Hot Yoga grosser Beliebtheit, insbesondere bei der internationalen Gemeinschaft, die diesen Stil aus den USA und Asien kennt.",
            "lausanne": "Lausanne bietet Hot-Yoga-Optionen für die sportbegeisterte Bevölkerung am Genfersee. Die intensive Praxis passt zur aktiven Lebensweise der Stadt.",
        },
        "who": "Hot Yoga ist für gesunde, belastbare Menschen geeignet, die eine intensive körperliche Herausforderung suchen. Anfänger sollten langsam beginnen und gut hydratisiert sein. Nicht empfohlen bei Herz-Kreislauf-Problemen, Schwangerschaft oder Hitzeempfindlichkeit.",
        "expect": "Bringe ein grosses Handtuch (für die Matte), ein kleines Handtuch (für den Schweiss) und mindestens 1 Liter Wasser mit. Bei Bikram dauert die Klasse 90 Minuten bei 40°C. Du wirst intensiv schwitzen. Die Hitze macht dich flexibler, aber auch schneller erschöpft. Plane Zeit zum Abkühlen danach ein.",
    },
    "kundalini": {
        "what": "Kundalini Yoga ist ein ganzheitlicher Yogastil, der körperliche Übungen mit Atemtechniken, Mantren, Mudras und Meditation verbindet. Ziel ist es, die Kundalini-Energie an der Basis der Wirbelsäule zu erwecken und durch die sieben Chakren aufsteigen zu lassen. Die Praxis ist sowohl spirituell als auch kraftvoll und transformativ.",
        "why_city": {
            "zuerich": "In Zürich hat Kundalini Yoga eine treue Gemeinschaft. Mehrere Studios bieten regelmässige Klassen an, und die Stadt beherbergt erfahrene Kundalini-Lehrer, die tiefe spirituelle Praxis vermitteln.",
            "basel": "Basel mit seiner offenen, kulturellen Atmosphäre bietet einen fruchtbaren Boden für Kundalini Yoga. Studios verbinden die spirituelle Praxis mit moderner Achtsamkeit.",
            "bern": "In Bern wird Kundalini Yoga von einer engagierten Community praktiziert. Die meditative Hauptstadt bietet den idealen Rahmen für diese spirituelle Yogaform.",
            "luzern": "Luzern bietet Kundalini-Yoga-Klassen in einer Umgebung, die Spiritualität und Natur verbindet. Die mystische Atmosphäre der Innerschweiz verstärkt die transformative Wirkung.",
            "genf": "Genfs vielfältige spirituelle Landschaft umfasst auch eine lebendige Kundalini-Community. Die Stadt bietet Klassen in Französisch und Englisch an.",
            "lausanne": "In Lausanne findet Kundalini Yoga seine Anhänger unter Menschen, die nach einer tieferen, spirituellen Yogapraxis suchen.",
        },
        "who": "Kundalini Yoga spricht Menschen an, die neben der körperlichen Praxis auch die spirituelle Dimension des Yoga erkunden möchten. Es sind keine Vorkenntnisse nötig. Besonders geeignet für Menschen, die Meditation, Atemarbeit und Selbsterfahrung suchen.",
        "expect": "Eine Kundalini-Klasse beginnt oft mit dem Mantra \"Ong Namo Guru Dev Namo\" und einer Einstimmung. Es folgt ein \"Kriya\" — eine spezifische Abfolge von Übungen, Atemtechniken und Haltungen. Weisse Kleidung und Kopfbedeckung sind traditionell, aber nicht Pflicht. Die Stunde endet mit einer Tiefenentspannung und dem Mantra \"Sat Nam\".",
    },
    "power": {
        "what": "Power Yoga ist ein kraftvoller, fitness-orientierter Yogastil, der auf Ashtanga Yoga basiert, aber ohne feste Sequenz arbeitet. Die Praxis legt den Fokus auf Kraft, Ausdauer und Flexibilität und bietet ein intensives Ganzkörpertraining. Power Yoga verbindet die Tradition des Yoga mit einem modernen, athletischen Ansatz.",
        "why_city": {
            "zuerich": "Im fitnessbegeisterten Zürich ist Power Yoga besonders populär. Studios bieten kraftvolle Klassen an, die sportliche Menschen ansprechen, die Yoga als Workout nutzen möchten.",
            "basel": "Basel bietet Power-Yoga-Klassen in mehreren Studios an. Die athletische Variante spricht besonders junge Berufstätige an, die ein intensives Training mit Yogaphilosophie verbinden wollen.",
            "bern": "In Bern finden Power-Yoga-Liebhaber ein wachsendes Angebot. Die Stadt bietet Klassen, die körperliche Herausforderung mit mentaler Stärkung verbinden.",
            "luzern": "Luzern bietet Power-Yoga-Klassen für alle, die Fitness und Yoga verbinden möchten. Die kraftvolle Praxis ergänzt das sportliche Angebot der Region perfekt.",
            "genf": "Genfs sportliche Bevölkerung schätzt Power Yoga als effizientes Ganzkörpertraining. Mehrere Studios bieten intensive Klassen auf Französisch und Englisch an.",
            "lausanne": "In der Sportstadt Lausanne ist Power Yoga eine natürliche Ergänzung zum aktiven Lebensstil. Studios bieten herausfordernde Klassen für fitness-orientierte Yogis.",
        },
        "who": "Power Yoga ist ideal für sportliche Menschen, die ein intensives Training suchen. Eine gewisse Grundfitness ist hilfreich, aber viele Studios bieten auch Einsteiger-Klassen an. Perfekt für alle, die Kraft aufbauen, Kalorien verbrennen und gleichzeitig flexibler werden möchten.",
        "expect": "Eine Power-Yoga-Klasse (60-75 Minuten) ist intensiv und schweisstreibend. Erwarte viele Plank-Variationen, Krieger-Posen, Arm-Balancen und Core-Arbeit. Das Tempo ist hoch, die Musik oft motivierend. Die Stunde fordert dich körperlich — plane Wasser und ein Handtuch ein.",
    },
    "aerial": {
        "what": "Aerial Yoga (Tuch-Yoga) nutzt ein von der Decke hängendes Tuch oder eine Hängematte als Hilfsmittel. Die Praxis kombiniert traditionelle Yoga-Posen mit akrobatischen Elementen und ermöglicht Umkehrhaltungen, Dekompressions-Übungen und spielerische Bewegungen in der Luft. Die Schwerelosigkeit entlastet Gelenke und Wirbelsäule.",
        "why_city": {
            "zuerich": "Zürich bietet einige der besten Aerial-Yoga-Studios der Schweiz. Die innovative Stadt hat diesen Trend früh aufgegriffen, und mehrere Studios haben spezielle Aerial-Räume mit professioneller Ausstattung.",
            "basel": "Basel hat eine überraschend starke Aerial-Yoga-Szene. Mehrere Studios bieten Tuch-Yoga an, vom Anfänger bis zum Fortgeschrittenen. Die kreative Stadt Basel ist ein perfekter Ort für diesen spielerischen Yogastil.",
            "bern": "In Bern wächst die Aerial-Yoga-Community. Studios bieten Kurse an, die Spass, Fitness und Yoga auf einzigartige Weise verbinden.",
            "luzern": "Luzern bietet Aerial-Yoga-Klassen, die ein ganz neues Körpergefühl vermitteln. Die Kombination aus Schwerelosigkeit und Yogapraxis begeistert in der Zentralschweiz.",
            "genf": "In Genf erfreut sich Aerial Yoga wachsender Beliebtheit. Die Stadt bietet Kurse in Studios mit professioneller Tuch-Ausstattung.",
            "lausanne": "Lausanne bietet Aerial-Yoga-Erlebnisse für alle, die Yoga von einer neuen Seite entdecken möchten. Die sportliche Stadt ist offen für innovative Yogaformen.",
        },
        "who": "Aerial Yoga ist für alle geeignet, die offen für Neues sind. Keine Yoga- oder Akrobatik-Erfahrung nötig. Besonders beliebt bei Menschen, die Höhenangst überwinden, ihre Wirbelsäule entlasten oder einfach Spass an ungewöhnlicher Bewegung haben.",
        "expect": "Du brauchst enganliegende Kleidung (keine Reissverschlüsse oder Knöpfe, die das Tuch beschädigen könnten). Die Klasse beginnt mit Aufwärmung am Boden, dann geht es ins Tuch. Du lernst Grundpositionen, schaukelst, hängst kopfüber und versuchst vielleicht sogar einen Aerial-Spagat. Es macht Spass — und trainiert den ganzen Körper.",
    },
    "prenatal": {
        "what": "Schwangerschaftsyoga (Prenatal Yoga) ist eine sanfte, speziell auf die Bedürfnisse von Schwangeren angepasste Yogapraxis. Die Übungen stärken den Beckenboden, lindern Rückenschmerzen, fördern die Atmung für die Geburt und schaffen einen Raum für bewusste Verbindung mit dem Baby. Alle Posen werden so modifiziert, dass sie in jeder Phase der Schwangerschaft sicher sind.",
        "why_city": {
            "zuerich": "Zürich bietet ein umfangreiches Schwangerschaftsyoga-Angebot. Zahlreiche Studios haben spezialisierte Prenatal-Kurse im Programm, oft geleitet von zertifizierten Hebammen oder Yogalehrerinnen mit Zusatzausbildung.",
            "basel": "In Basel finden werdende Mütter ein herzliches Schwangerschaftsyoga-Angebot. Mehrere Studios bieten spezialisierte Kurse an, die auch als Geburtsvorbereitungsergänzung dienen.",
            "bern": "Bern hat eine starke Schwangerschaftsyoga-Community. Studios bieten wöchentliche Kurse an, die Schwangere durch alle Trimester begleiten und auf die Geburt vorbereiten.",
            "luzern": "In Luzern finden Schwangere liebevoll gestaltete Prenatal-Yoga-Kurse, die Körper und Geist auf die Geburt vorbereiten. Die ruhige Atmosphäre der Stadt ist ideal dafür.",
            "genf": "Genf bietet Schwangerschaftsyoga in mehreren Studios an, oft zweisprachig (Französisch/Englisch). Die internationale Gemeinschaft schätzt dieses spezielle Angebot sehr.",
            "lausanne": "In Lausanne unterstützen Prenatal-Yoga-Kurse Schwangere auf ihrem Weg. Studios bieten sanfte Klassen, die Wohlbefinden und Gemeinschaft fördern.",
        },
        "who": "Schwangerschaftsyoga ist für alle werdenden Mütter geeignet — unabhängig von Yoga-Erfahrung. In der Regel ab dem zweiten Trimester empfohlen. Rücksprache mit der Ärztin oder Hebamme ist sinnvoll. Die Kurse bieten auch eine wertvolle Gemeinschaft unter Gleichgesinnten.",
        "expect": "Eine Prenatal-Yoga-Klasse (60-75 Minuten) umfasst sanfte Dehnungen, Beckenbodenübungen, Atemtechniken für die Geburt und Entspannung. Die Atmosphäre ist warm und unterstützend. Viele Studios bieten nach der Geburt auch Postnatal-Yoga mit Baby an.",
    },
    "restorative": {
        "what": "Restorative Yoga ist ein zutiefst entspannender Yogastil, bei dem der Körper mit Hilfsmitteln wie Bolstern, Decken, Blöcken und Gurten in bequemen Positionen vollständig unterstützt wird. Die wenigen Posen (4-6 pro Klasse) werden 10-20 Minuten gehalten. Ziel ist die Aktivierung des Parasympathikus — des Ruhe- und Regenerationssystems des Körpers.",
        "why_city": {
            "zuerich": "Im stressigen Zürcher Alltag ist Restorative Yoga ein wahrer Segen. Studios bieten diese heilsame Praxis besonders am Abend und am Wochenende an — der perfekte Gegenpol zur Hektik der Grossstadt.",
            "basel": "Basel bietet Restorative Yoga als wohltuenden Ausgleich zum Arbeitsalltag. Studios integrieren diese Praxis oft mit Klangschalen oder ätherischen Ölen für ein vollständiges Entspannungserlebnis.",
            "bern": "In Bern ist Restorative Yoga besonders in den kälteren Monaten beliebt. Die kuschelige Praxis mit vielen Decken und Kissen bietet Geborgenheit und tiefe Regeneration.",
            "luzern": "Luzern mit seinem Fokus auf Wohlbefinden bietet Restorative Yoga als ganzheitliche Entspannungsmethode. Die Studios am See schaffen eine Oase der Ruhe.",
            "genf": "In Genf suchen viele Berufstätige aus internationalen Organisationen nach Restorative Yoga als Ausgleich. Die Stadt bietet Klassen, die Körper und Geist regenerieren.",
            "lausanne": "Lausanne bietet Restorative-Yoga-Klassen, die den gestressten Körper sanft in die Entspannung führen. Die Studios am Genfersee verstärken den heilenden Effekt.",
        },
        "who": "Restorative Yoga ist für absolut jeden geeignet. Es ist besonders wertvoll für gestresste Menschen, bei Burnout, chronischen Schmerzen, Schlafproblemen oder nach Verletzungen. Keine Vorkenntnisse, keine Fitness nötig — nur die Bereitschaft, loszulassen.",
        "expect": "Bringe warme Socken und bequeme Kleidung mit. Du wirst in 4-6 Positionen mit Hilfsmitteln gebettet und liegst dort jeweils 10-20 Minuten. Es gibt kaum aktive Bewegung. Der Raum ist warm, das Licht gedimmt, oft erklingt sanfte Musik. Manche schlafen ein — und das ist völlig in Ordnung.",
    },
}


def load_json(path):
    """Load JSON file, return empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not load {path}: {e}")
        return {}


def load_studios(file_key):
    """Load studios for a canton."""
    path = os.path.join(DATA_DIR, f"studios_{file_key}.json")
    data = load_json(path)
    studios = data.get("studios", [])
    return [s for s in studios if s.get("active", True)]


def studio_matches_style(studio, style):
    """Check if a studio offers a given style (fuzzy matching)."""
    studio_styles = [s.lower().strip() for s in studio.get("styles", [])]
    # Also check special_features for some styles
    features = [f.lower().strip() for f in studio.get("special_features", [])]
    all_terms = studio_styles + features

    for term in style["match_terms"]:
        for studio_term in all_terms:
            if term.lower() in studio_term or studio_term in term.lower():
                return True
    return False


def get_other_styles_text(studio, current_style):
    """Get other styles offered by a studio."""
    styles = studio.get("styles", [])
    other = [s for s in styles if s.lower() not in [t.lower() for t in current_style["match_terms"]]]
    return ", ".join(other[:6]) if other else ""


def make_address_string(studio):
    """Get the first address as a string."""
    addrs = studio.get("addresses", [])
    if not addrs:
        return ""
    a = addrs[0]
    parts = []
    if a.get("street"):
        parts.append(a["street"])
    if a.get("zip") or a.get("city"):
        parts.append(f"{a.get('zip', '')} {a.get('city', '')}".strip())
    return ", ".join(parts)


def escape(text):
    """HTML-escape text."""
    return html.escape(str(text))


def generate_page_html(style, city, matching_studios, all_styles, all_cities):
    """Generate the full HTML for one style+city landing page."""
    style_name = style["display"]
    city_name = city["name"]
    city_slug = city["url_slug"]
    style_slug = style["url_slug"]
    folder_name = f"{style_slug}-{city_slug}"
    page_url = f"{BASE_URL}/yoga/{folder_name}/"
    canton_url = f"{BASE_URL}/kanton/{city['canton_id']}/"
    num_studios = len(matching_studios)

    desc_data = STYLE_DESCRIPTIONS[style["description_key"]]
    city_why = desc_data["why_city"].get(city_slug, desc_data["why_city"].get("zuerich", ""))

    title = f"{style_name} in {city_name} — Alle Studios & Kurse | Yoga Schweiz"
    meta_desc = f"{style_name} in {city_name}: {num_studios} Studio{'s' if num_studios != 1 else ''} mit {style_name}-Kursen. Adressen, Stile und Links. Finde deinen perfekten Kurs."
    meta_keywords = f"{style_name} {city_name}, {style['name']} Yoga {city_name}, {style['name']} Yoga Schweiz, Yoga {city_name}"

    # Build studio cards
    studio_cards = ""
    for s in matching_studios:
        addr = escape(make_address_string(s))
        other_styles = escape(get_other_styles_text(s, style))
        website = s.get("website", "")
        studio_cards += f"""
            <div class="studio-card">
                <h3><a href="{canton_url}" class="studio-link">{escape(s['name'])}</a></h3>
                <p class="studio-address">{addr}</p>
                {'<p class="studio-other-styles">Weitere Stile: ' + other_styles + '</p>' if other_styles else ''}
                {'<a href="' + escape(website) + '" target="_blank" rel="noopener noreferrer" class="studio-website">Website besuchen &rarr;</a>' if website else ''}
            </div>"""

    # Related styles (same city, different style)
    related_links = ""
    for other_style in all_styles:
        if other_style["url_slug"] == style_slug:
            continue
        other_folder = f"{other_style['url_slug']}-{city_slug}"
        related_links += f'<a href="{BASE_URL}/yoga/{other_folder}/" class="related-link">{other_style["display"]}</a>\n'

    # Same style other cities
    other_city_links = ""
    for other_city in all_cities:
        if other_city["url_slug"] == city_slug:
            continue
        other_folder = f"{style_slug}-{other_city['url_slug']}"
        other_city_links += f'<a href="{BASE_URL}/yoga/{other_folder}/" class="related-link">{style_name} in {other_city["name"]}</a>\n'

    page_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(meta_desc)}">
    <meta name="keywords" content="{escape(meta_keywords)}">
    <meta name="author" content="YogaSchweiz">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{page_url}">

    <!-- Open Graph -->
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(meta_desc)}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{page_url}">
    <meta property="og:locale" content="de_CH">
    <meta property="og:site_name" content="Yoga Schweiz">

    <!-- Schema.org Article -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{style_name} in {city_name}",
      "description": "{escape(meta_desc)}",
      "url": "{page_url}",
      "author": {{
        "@type": "Organization",
        "name": "YogaSchweiz"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "YogaSchweiz",
        "url": "{BASE_URL}/"
      }},
      "inLanguage": "de",
      "datePublished": "2026-03-21",
      "dateModified": "{date.today().isoformat()}",
      "about": {{
        "@type": "Thing",
        "name": "{style_name}"
      }}
    }}
    </script>

    <!-- Schema.org BreadcrumbList -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "{BASE_URL}/"
        }},
        {{
          "@type": "ListItem",
          "position": 2,
          "name": "Yoga-Stile",
          "item": "{BASE_URL}/yoga/"
        }},
        {{
          "@type": "ListItem",
          "position": 3,
          "name": "{style_name} in {city_name}",
          "item": "{page_url}"
        }}
      ]
    }}
    </script>

    <link rel="stylesheet" href="../../css/fonts.css">

    <style>
        :root {{
            --primary: #6B5B95;
            --primary-light: #8B7BB5;
            --primary-dark: #4A3D6E;
            --accent: #D4A373;
            --accent-light: #E8C9A0;
            --bg: #FAFAF8;
            --bg-card: #FFFFFF;
            --text: #2D2D2D;
            --text-light: #6B6B6B;
            --border: #E8E4E0;
            --radius: 12px;
            --shadow: 0 2px 12px rgba(107, 91, 149, 0.08);
            --shadow-hover: 0 4px 20px rgba(107, 91, 149, 0.15);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
        }}

        h1, h2, h3 {{
            font-family: 'Playfair Display', Georgia, serif;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .header-inner {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header a {{
            color: #fff;
            text-decoration: none;
            font-weight: 500;
        }}

        .header .logo {{
            font-family: 'Playfair Display', serif;
            font-size: 1.3rem;
            font-weight: 700;
        }}

        .header nav a {{
            margin-left: 1.5rem;
            font-size: 0.95rem;
            opacity: 0.9;
            transition: opacity 0.2s;
        }}

        .header nav a:hover {{
            opacity: 1;
            text-decoration: underline;
        }}

        /* Breadcrumb */
        .breadcrumb {{
            max-width: 1100px;
            margin: 1.5rem auto 0;
            padding: 0 1.5rem;
            font-size: 0.9rem;
            color: var(--text-light);
        }}

        .breadcrumb a {{
            color: var(--primary);
            text-decoration: none;
        }}

        .breadcrumb a:hover {{
            text-decoration: underline;
        }}

        .breadcrumb span {{
            margin: 0 0.4rem;
        }}

        /* Hero */
        .hero {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem 2rem;
        }}

        .hero h1 {{
            font-size: 2.5rem;
            color: var(--primary-dark);
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }}

        .hero .subtitle {{
            font-size: 1.15rem;
            color: var(--text-light);
        }}

        .hero .studio-count {{
            display: inline-block;
            background: var(--accent-light);
            color: var(--primary-dark);
            padding: 0.3rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.95rem;
            margin-top: 0.8rem;
        }}

        /* Content sections */
        .content {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 1.5rem 3rem;
        }}

        .section {{
            margin-bottom: 2.5rem;
        }}

        .section h2 {{
            font-size: 1.6rem;
            color: var(--primary-dark);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent);
        }}

        .description p {{
            margin-bottom: 1rem;
            font-size: 1.05rem;
            color: var(--text);
        }}

        /* Studio cards */
        .studios-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.2rem;
        }}

        .studio-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            transition: box-shadow 0.3s, transform 0.2s;
        }}

        .studio-card:hover {{
            box-shadow: var(--shadow-hover);
            transform: translateY(-2px);
        }}

        .studio-card h3 {{
            font-size: 1.15rem;
            color: var(--primary-dark);
            margin-bottom: 0.5rem;
        }}

        .studio-link {{
            color: var(--primary);
            text-decoration: none;
        }}

        .studio-link:hover {{
            text-decoration: underline;
        }}

        .studio-address {{
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 0.4rem;
        }}

        .studio-other-styles {{
            font-size: 0.85rem;
            color: var(--text-light);
            margin-bottom: 0.5rem;
        }}

        .studio-website {{
            display: inline-block;
            color: var(--accent);
            font-weight: 600;
            text-decoration: none;
            font-size: 0.9rem;
            margin-top: 0.3rem;
        }}

        .studio-website:hover {{
            color: var(--primary);
        }}

        /* Related links */
        .related-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }}

        .related-link {{
            display: inline-block;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            color: var(--primary);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: background 0.2s, border-color 0.2s;
        }}

        .related-link:hover {{
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }}

        /* Footer */
        .footer {{
            background: var(--primary-dark);
            color: #fff;
            padding: 2.5rem 1.5rem;
            text-align: center;
        }}

        .footer a {{
            color: var(--accent-light);
            text-decoration: none;
            margin: 0 0.8rem;
        }}

        .footer a:hover {{
            text-decoration: underline;
        }}

        .footer p {{
            margin-top: 1rem;
            font-size: 0.85rem;
            opacity: 0.7;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 1.8rem;
            }}
            .studios-grid {{
                grid-template-columns: 1fr;
            }}
            .header-inner {{
                flex-direction: column;
                gap: 0.5rem;
            }}
        }}
    </style>
</head>
<body>

    <!-- Header -->
    <header class="header">
        <div class="header-inner">
            <a href="{BASE_URL}/" class="logo">Yoga Schweiz</a>
            <nav>
                <a href="{BASE_URL}/">Home</a>
                <a href="{BASE_URL}/kanton/">Kantone</a>
                <a href="{canton_url}">{escape(city_name)}</a>
            </nav>
        </div>
    </header>

    <!-- Breadcrumb -->
    <div class="breadcrumb">
        <a href="{BASE_URL}/">Home</a>
        <span>&rsaquo;</span>
        <a href="{BASE_URL}/yoga/">Yoga-Stile</a>
        <span>&rsaquo;</span>
        {escape(style_name)} in {escape(city_name)}
    </div>

    <!-- Hero -->
    <section class="hero">
        <h1>{escape(style_name)} in {escape(city_name)}</h1>
        <p class="subtitle">Alle Studios und Kurse f&uuml;r {escape(style_name)} in {escape(city_name)} auf einen Blick</p>
        <span class="studio-count">{num_studios} Studio{'s' if num_studios != 1 else ''}</span>
    </section>

    <!-- Content -->
    <main class="content">

        <!-- Description -->
        <section class="section description">
            <h2>&Uuml;ber {escape(style_name)}</h2>
            <p>{desc_data['what']}</p>
            <p>{city_why}</p>
            <p><strong>F&uuml;r wen:</strong> {desc_data['who']}</p>
            <p><strong>Was erwartet dich:</strong> {desc_data['expect']}</p>
        </section>

        <!-- Studios -->
        <section class="section">
            <h2>Studios mit {escape(style_name)} in {escape(city_name)}</h2>
            <div class="studios-grid">
                {studio_cards}
            </div>
        </section>

        <!-- Related styles in same city -->
        <section class="section">
            <h2>Weitere Yoga-Stile in {escape(city_name)}</h2>
            <div class="related-grid">
                {related_links}
            </div>
        </section>

        <!-- Same style in other cities -->
        <section class="section">
            <h2>{escape(style_name)} in anderen St&auml;dten</h2>
            <div class="related-grid">
                {other_city_links}
            </div>
        </section>

        <!-- Blog articles -->
        <section class="section">
            <h2>Lesenswerte Artikel</h2>
            <div class="related-grid">
                <a href="../../blog/yoga-stile-vergleich/" class="related-link">Yoga-Stile im Vergleich</a>
                <a href="../../blog/yoga-fuer-anfaenger/" class="related-link">Yoga f&uuml;r Anf&auml;nger</a>
                <a href="../../blog/yoga-preise-schweiz-2026/" class="related-link">Yoga-Preise Schweiz 2026</a>
            </div>
        </section>

    </main>

    <!-- Footer -->
    <footer class="footer">
        <div>
            <a href="{BASE_URL}/">Home</a>
            <a href="{BASE_URL}/kanton/">Alle Kantone</a>
            <a href="{canton_url}">Yoga in {escape(city_name)}</a>
        </div>
        <p>&copy; 2026 Yoga Schweiz &mdash; Alle Angaben ohne Gew&auml;hr</p>
    </footer>

</body>
</html>"""
    return page_html


def main():
    print("=" * 60)
    print("Generating Yoga Style + City landing pages")
    print("=" * 60)

    # Load studios for each city
    city_studios = {}
    for city in CITIES:
        studios = load_studios(city["file_key"])
        city_studios[city["url_slug"]] = studios
        print(f"  Loaded {len(studios)} studios for {city['name']}")

    # Track which style+city combos have pages (for cross-linking, only link to existing pages)
    existing_combos = set()
    pages_to_generate = []

    # First pass: determine which pages will exist
    for style in STYLES:
        for city in CITIES:
            studios = city_studios[city["url_slug"]]
            matching = [s for s in studios if studio_matches_style(s, style)]
            if matching:
                existing_combos.add((style["url_slug"], city["url_slug"]))
                pages_to_generate.append((style, city, matching))

    print(f"\n  Found {len(pages_to_generate)} style+city combinations with studios\n")

    # Filter related links to only existing pages
    existing_style_slugs_per_city = defaultdict(list)
    existing_city_slugs_per_style = defaultdict(list)
    for s_slug, c_slug in existing_combos:
        # Find the style and city objects
        style_obj = next((s for s in STYLES if s["url_slug"] == s_slug), None)
        city_obj = next((c for c in CITIES if c["url_slug"] == c_slug), None)
        if style_obj:
            existing_style_slugs_per_city[c_slug].append(style_obj)
        if city_obj:
            existing_city_slugs_per_style[s_slug].append(city_obj)

    # Second pass: generate pages
    generated = 0
    for style, city, matching_studios in pages_to_generate:
        folder_name = f"{style['url_slug']}-{city['url_slug']}"
        out_dir = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(out_dir, exist_ok=True)

        # Only pass styles/cities that actually have pages
        available_styles = existing_style_slugs_per_city[city["url_slug"]]
        available_cities = existing_city_slugs_per_style[style["url_slug"]]

        page_html = generate_page_html(style, city, matching_studios, available_styles, available_cities)

        out_path = os.path.join(out_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)

        generated += 1
        print(f"  [{generated:2d}] {style['display']:25s} in {city['name']:10s} ({len(matching_studios)} studios) -> yoga/{folder_name}/")

    print(f"\n{'=' * 60}")
    print(f"  Generated {generated} landing pages in {OUTPUT_DIR}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
