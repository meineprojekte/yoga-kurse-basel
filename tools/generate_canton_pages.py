#!/usr/bin/env python3
"""
Generate static HTML pages for all 26 Swiss cantons.
Reads data from data/ directory and generates kanton/{canton_id}/index.html pages.
"""

import json
import os
import glob
import html
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "kanton")
BASE_URL = "https://meineprojekte.github.io/yoga-kurse-basel"

# --- Canton ID to data file key mapping ---
# Most canton IDs match file names, but "basel-stadt" maps to "basel"
def get_file_key(canton_id):
    """Map canton ID to the key used in filenames."""
    mapping = {
        "basel-stadt": "basel",
    }
    return mapping.get(canton_id, canton_id)


# --- Data loading ---
def load_json(path):
    """Load JSON file, return empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not load {path}: {e}")
        return {}


def load_cantons():
    """Load cantons.json."""
    data = load_json(os.path.join(DATA_DIR, "cantons.json"))
    return data.get("cantons", [])


def load_studios(file_key):
    """Load studios for a canton."""
    path = os.path.join(DATA_DIR, f"studios_{file_key}.json")
    data = load_json(path)
    studios = data.get("studios", [])
    # Filter only active studios
    return [s for s in studios if s.get("active", True)]


def load_schedule(file_key):
    """Load schedule for a canton."""
    path = os.path.join(DATA_DIR, f"schedule_{file_key}.json")
    data = load_json(path)
    return data.get("classes", [])


# --- Canton descriptions (unique German text for each canton) ---
CANTON_DESCRIPTIONS = {
    "zurich": [
        "Zürich ist das pulsierende Zentrum der Schweizer Yoga-Szene. Als grösste Stadt des Landes bietet der Kanton eine beeindruckende Vielfalt an Yoga-Studios — von etablierten Schulen in der Altstadt bis hin zu modernen Boutique-Studios im Kreis 4 und 5. Ob Power Vinyasa in einem Loft mit Blick über die Dächer, meditatives Yin Yoga am Zürichsee oder traditionelles Ashtanga in einem historischen Gebäude — hier findet jeder seinen Stil.",
        "Die Yoga-Community in Zürich ist international geprägt. Viele Studios bieten Kurse auf Deutsch und Englisch an, manche auch auf Französisch oder Spanisch. Besonders beliebt sind Lunch-Yoga-Klassen im Geschäftsviertel, After-Work-Sessions und Wochenend-Workshops mit internationalen Gastlehrern. Die Stadt zieht regelmässig bekannte Yoga-Lehrer aus aller Welt an.",
        "Neben der Stadt Zürich bieten auch Winterthur, Uster, Wädenswil und weitere Gemeinden im Kanton ein breites Yoga-Angebot. Besonders im Sommer locken Outdoor-Yoga-Events am See und in den Parks. Von Anfängerkursen bis zu Teacher Trainings — der Kanton Zürich lässt keine Wünsche offen.",
        "Die beliebtesten Yoga-Stile in Zürich sind Vinyasa Flow, Hatha Yoga und Yin Yoga. Aber auch spezialisierte Richtungen wie Ashtanga in der Mysore-Tradition, Iyengar mit Fokus auf Alignment, Kundalini Yoga und Hot Yoga (Bikram) haben in Zürich eine treue Anhängerschaft. Mehrere Studios bieten zudem therapeutisches Yoga, Yoga für Schwangere und Yoga für Kinder an — das Angebot wächst stetig.",
        "Wer zum ersten Mal ein Yoga-Studio in Zürich besucht, findet in den meisten Studios Probeabonnements oder vergünstigte Einstiegsangebote. Viele Studios haben offene Klassen ohne Voranmeldung (Drop-in), was den Einstieg besonders einfach macht. Die Preise für eine Einzellektion liegen je nach Studio zwischen CHF 25 und CHF 40. Zehnerkarten und Monatsabos bieten deutliche Ersparnisse für regelmässige Besucher.",
        "Zürich hat sich auch als Standort für Yoga-Lehrerausbildungen (Teacher Training) etabliert. Mehrere Studios bieten 200-Stunden und 500-Stunden Yoga-Alliance-zertifizierte Ausbildungen an, die angehenden Lehrern eine fundierte Grundlage bieten. Internationale Lehrer kommen regelmässig für Workshops und Intensives in die Stadt.",
        "Mit über 40 Studios und Hunderten von wöchentlichen Klassen ist Zürich der ideale Ort, um Yoga in all seinen Facetten zu erleben. Die kurzen Wege dank exzellentem öffentlichem Verkehr machen es leicht, verschiedene Studios und Stile auszuprobieren — ob in der Langstrasse, in Oerlikon oder am See."
    ],
    "bern": [
        "Die Bundesstadt Bern verbindet Geschichte mit einer lebendigen Yoga-Kultur. In der UNESCO-Welterbe-Altstadt und den umliegenden Quartieren finden sich zahlreiche Studios, die von traditionellem Hatha bis zu modernem Aerial Yoga alles anbieten. Die entspannte Atmosphäre der Stadt spiegelt sich in der Yoga-Szene wider — hier geht es weniger um Trends als um echte Praxis.",
        "Bern ist bekannt für seine starke Iyengar-Yoga-Tradition und eine wachsende Kundalini-Szene. Viele Studios legen Wert auf kleine Gruppen und persönliche Betreuung. Neben der Hauptstadt bieten auch Thun, Biel/Bienne, Burgdorf und Langenthal ein vielfältiges Angebot. Die zweisprachige Region (Deutsch/Französisch) macht das Angebot besonders zugänglich.",
        "Besonders reizvoll ist Yoga in Bern durch die Nähe zur Natur. Yoga-Retreats im Berner Oberland, Meditationskurse mit Blick auf Eiger, Mönch und Jungfrau oder Yoga am Thunersee — die Region verbindet urbanes Angebot mit alpiner Ruhe. Der Kanton Bern ist ein perfekter Ort für alle, die Yoga und Natur verbinden möchten.",
        "Die Preise für Yoga-Kurse in Bern sind etwas günstiger als in Zürich und Genf. Eine Einzellektion kostet zwischen CHF 20 und CHF 35, und viele Studios bieten Einsteiger-Specials an — etwa eine Woche unlimitiert für CHF 30–50. Wer sich langfristig binden möchte, findet bei vielen Studios attraktive Monatsabos zwischen CHF 120 und CHF 200.",
        "Anfänger finden in Bern ein besonders einladendes Umfeld. Die Berner Yogaszene legt grossen Wert auf Achtsamkeit und Qualität statt Grösse und Tempo. Viele Lehrer sind in der Kripalu-, Sivananda- oder Iyengar-Tradition ausgebildet und bieten einen präzisen, anatomisch fundierten Unterricht. Ob sanftes Restorative Yoga für Stressabbau oder kraftvolles Power Yoga für Fitness — Bern hat für jeden das passende Angebot."
    ],
    "luzern": [
        "Luzern, die Leuchtenstadt am Vierwaldstättersee, bietet eine wunderbar inspirierende Kulisse für Yoga. Die Kombination aus Seeblick, Bergpanorama und mittelalterlicher Altstadt schafft eine einzigartige Atmosphäre für die Praxis. Studios in der Nähe des Sees nutzen das natürliche Licht und die Ruhe des Wassers als Teil ihres Konzepts.",
        "Die Yoga-Szene in Luzern ist vielfältig und wächst stetig. Von dynamischem Vinyasa Flow über sanftes Yin Yoga bis zu therapeutischem Yoga — die Studios decken ein breites Spektrum ab. Besonders beliebt sind Yoga-Kurse für Berufstätige sowie Angebote für Senioren. Auch in Kriens, Emmen und Horw finden sich engagierte Yoga-Lehrer.",
        "Im Sommer locken Outdoor-Yoga-Sessions am See und auf den umliegenden Bergen. Luzern ist zudem ein beliebter Ausgangspunkt für Yoga-Retreats in der Zentralschweiz. Die Stadt verbindet städtisches Flair mit der Gelassenheit der Innerschweiz — ideal für eine bewusste Yoga-Praxis.",
        "Mit rund 16 Studios bietet der Kanton Luzern ein kompaktes, aber hochwertiges Angebot. Viele Lehrer haben internationale Ausbildungen und bringen frische Impulse in die lokale Szene.",
        "Yoga-Anfänger in Luzern profitieren von der persönlichen Atmosphäre der Studios. Im Gegensatz zu den anonymen Grossstadt-Studios kennen die Lehrer hier ihre Schüler persönlich und können auf individuelle Bedürfnisse eingehen. Beliebte Einstiegsstile sind Hatha Yoga für eine solide Grundlage und Yin Yoga für tiefe Entspannung. Eine Einzellektion kostet in Luzern CHF 20 bis CHF 35.",
        "Die kulturelle Vielfalt Luzerns — von der klassischen Musik (KKL) über die Fasnacht bis zur innovativen Kunstszene — bereichert auch das Yoga-Angebot. Einige Studios verbinden Yoga mit Klang (Sound Healing), Meditation oder Atemarbeit (Breathwork). Die Stadt bietet damit ein ganzheitliches Wellness-Angebot, das über die reine Yoga-Praxis hinausgeht."
    ],
    "basel-stadt": [
        "Basel-Stadt ist die Wiege dieses Projekts und verfügt über eine der dichtesten Yoga-Landschaften der Schweiz. Auf kleinem Raum vereint der Stadtkanton über 30 Studios mit einem unglaublich vielfältigen Angebot. Vom eleganten Studio mit Rheinblick bis zum gemütlichen Quartier-Studio in Kleinbasel — die Yogaszene in Basel ist so bunt wie die Stadt selbst.",
        "Besonders bemerkenswert ist die internationale Ausrichtung der Basler Yoga-Studios. Dank der Grenznähe zu Deutschland und Frankreich und der Präsenz internationaler Organisationen wie Novartis, Roche und der Universität Basel unterrichten viele Studios auf Deutsch und Englisch. Stile wie Jivamukti, Katonah und Embodied Flow, die man sonst nur in Grossstädten findet, sind hier vertreten.",
        "Die Basler Yoga-Community zeichnet sich durch Offenheit und Zusammenarbeit aus. Regelmässige Events wie Yoga am Rhein, Community-Klassen und Workshops bringen Praktizierende zusammen. Viele Studios bieten Drop-in-Klassen an, was Basel besonders gastfreundlich für Yoga-Reisende macht.",
        "Von Ashtanga und Iyengar über Vinyasa und Hot Yoga bis zu Prenatal und Kinderyoga — Basel bietet für jede Lebensphase und jeden Geschmack das passende Angebot. Die kurzen Wege in der kompakten Stadt machen es leicht, verschiedene Studios und Stile auszuprobieren.",
        "Für Yoga-Anfänger in Basel empfiehlt es sich, zuerst einen Hatha- oder Vinyasa-Einsteigerkurs zu besuchen. Viele Studios wie B.Yoga, Yogawald und Lotos Yoga-Zentrum bieten spezielle Beginner-Klassen an, in denen Grundhaltungen (Asanas), Atemtechniken (Pranayama) und Entspannung geduldig erklärt werden. Die meisten Studios bieten eine kostenlose Probestunde oder ein vergünstigtes Intro-Paket an.",
        "Die Preise für Yoga in Basel liegen bei CHF 20 bis 40 für eine Einzellektion. Wer regelmässig praktiziert, spart mit einer 10er-Karte (CHF 200–350) oder einem Monatsabo (CHF 150–250). Einige Studios wie das Yoga-Studio Breath in Kleinbasel bieten auch Solidaritätspreise an, damit Yoga für alle zugänglich bleibt. Buchungsplattformen wie Eversports vereinfachen die Reservierung.",
        "Neben klassischen Indoor-Studios hat Basel auch eine lebendige Outdoor-Yoga-Szene. Im Sommer finden am Rheinufer, im Schützenmattpark und auf dem Münsterplatz regelmässig kostenlose oder kostengünstige Community-Yoga-Sessions statt. Die Rheinschwimmen-Kultur und die entspannte Atmosphäre machen Basel zu einem einzigartigen Ort, um Yoga im Freien zu erleben."
    ],
    "geneve": [
        "Genf, die internationale Stadt am Lac Léman, bietet eine kosmopolitische Yoga-Szene. Die Präsenz internationaler Organisationen wie der UNO, des IKRK und zahlreicher multinationaler Unternehmen hat eine vielfältige Community geschaffen, die sich auch in den Yoga-Studios widerspiegelt. Kurse werden häufig auf Französisch, Englisch und manchmal auch auf weiteren Sprachen angeboten.",
        "Die Yoga-Studios in Genf zeichnen sich durch hohe Qualität und internationale Standards aus. Von klassischem Hatha und Ashtanga über Bikram und Hot Yoga bis zu innovativen Formaten wie Yoga mit Live-Musik — das Angebot ist so vielfältig wie die Stadt selbst. Besonders beliebt sind Studios in den Quartieren Eaux-Vives, Plainpalais und Carouge.",
        "Am Ufer des Genfersees und in den Parks der Stadt finden im Sommer zahlreiche Outdoor-Yoga-Events statt. Genf ist zudem ein Zentrum für Yoga-Ausbildungen und Workshops mit internationalen Gastlehrern. Die Stadt verbindet französische Lebensart mit schweizerischer Präzision — eine perfekte Mischung für eine bewusste Yoga-Praxis.",
        "Mit rund 18 Studios bietet Genf eines der grössten Yoga-Angebote der Romandie. Die Vielfalt der Stile und die Internationalität machen die Stadt zu einem besonderen Yoga-Standort in der Schweiz.",
        "Für Anfänger in Genf gibt es zahlreiche Einstiegsmöglichkeiten. Die meisten Studios bieten Cours d'initiation oder Beginner-Serien an, die über 4–8 Wochen die Grundlagen von Hatha oder Vinyasa Yoga vermitteln. Preise für eine Einzellektion liegen bei CHF 25 bis CHF 40, Monatsabos bei CHF 150 bis CHF 250. Viele Studios akzeptieren Buchungen über ClassPass.",
        "Genf zeichnet sich auch durch spezialisierte Angebote aus: Yoga für Diplomaten und internationale Fachkräfte, Yoga-Therapie bei chronischen Beschwerden, Prenatal- und Postpartum-Yoga sowie Yoga für Senioren. Mehrere Studios bieten zudem Corporate-Yoga-Programme an, die in den Büros internationaler Organisationen stattfinden. Die Stadt ist ein Schmelztiegel der Yoga-Traditionen."
    ],
    "vaud": [
        "Der Kanton Waadt mit seiner Hauptstadt Lausanne bietet eine lebendige Yoga-Szene am Genfersee. Lausanne, die olympische Hauptstadt, verbindet Sport und Wohlbefinden auf natürliche Weise. Die hügelige Topografie der Stadt und der Blick auf den See und die Alpen schaffen eine inspirierende Umgebung für die Yoga-Praxis.",
        "Neben Lausanne bieten auch Montreux, Vevey, Nyon und Morges ein breites Yoga-Angebot. Die Weinberge des Lavaux (UNESCO-Welterbe) bilden eine traumhafte Kulisse für Yoga-Retreats und Outdoor-Sessions. Die Szene ist mehrheitlich französischsprachig, viele Studios bieten aber auch Kurse auf Englisch an.",
        "Von klassischem Hatha über dynamisches Vinyasa bis zu Kundalini und Yoga Nidra — die Waadtländer Studios decken ein breites Spektrum ab. Besonders beliebt sind Yoga-Angebote in Kombination mit Wandern, Segeln oder Weinverkostungen. Der Kanton Waadt verbindet Genuss mit Achtsamkeit.",
        "Mit 16 Studios ist das Angebot in der Waadt vielfältig und gut verteilt. Die Nähe zur Natur und die kulturelle Vielfalt der Region machen den Kanton zu einem attraktiven Yoga-Standort.",
        "Für Neueinsteiger bieten die Waadtländer Studios oft vergünstigte Einstiegswochen oder Schnupperstunden an. Die Preise liegen etwas unter dem Genfer Niveau: Eine Einzellektion kostet CHF 22 bis CHF 35, und Monatsabos sind ab CHF 120 erhältlich. Die entspannte, unkomplizierte Atmosphäre der Romande-Studios macht den Einstieg besonders angenehm.",
        "Lausanne hat sich zudem als Zentrum für Yoga-Events in der Westschweiz etabliert. Das jährliche Yoga-Festival am Genfersee, Workshops mit internationalen Lehrern und Yoga-Brunches in den Cafés der Stadt ziehen Praktizierende aus der ganzen Region an. Der Kanton Waadt verbindet französische Gelassenheit mit schweizerischer Qualität — eine ideale Kombination für die Yoga-Praxis."
    ],
    "uri": [
        "Der Kanton Uri, im Herzen der Schweiz gelegen, bietet Yoga in einer atemberaubenden Berglandschaft. Obwohl der Kanton klein ist, hat sich hier eine engagierte Yoga-Community entwickelt. In Altdorf, dem Hauptort, finden Yoga-Begeisterte verschiedene Angebote von Hatha über Vinyasa bis zu Meditation und Breathwork.",
        "Die Nähe zur Natur ist das grosse Plus von Yoga in Uri. Die majestätischen Berge, der Urnersee und die ruhige Atmosphäre schaffen ideale Bedingungen für eine vertiefte Praxis. Die Studios hier legen besonderen Wert auf persönliche Betreuung und ganzheitliche Ansätze."
    ],
    "schwyz": [
        "Der Kanton Schwyz, Namensgeber der Schweiz, bietet Yoga zwischen See und Bergen. Die zentrale Lage und die malerische Landschaft mit dem Vierwaldstättersee und dem Ägerisee machen die Region zu einem besonderen Ort für Yoga-Praktizierende.",
        "Die Yoga-Studios in Schwyz zeichnen sich durch persönliche Atmosphäre und naturnahe Angebote aus. Ob in der Hauptstadt Schwyz oder in Einsiedeln mit seinem berühmten Kloster — hier findet Yoga in einer Umgebung statt, die zur inneren Einkehr einlädt."
    ],
    "obwalden": [
        "Obwalden, der idyllische Halbkanton am Sarnersee, bietet Yoga in einer der ruhigsten Ecken der Schweiz. Die Kombination aus Alpenpanorama und Seenlandschaft schafft perfekte Bedingungen für eine achtsame Praxis.",
        "Trotz seiner geringen Grösse verfügt Obwalden über engagierte Yoga-Lehrer, die ein qualitativ hochwertiges Angebot bieten. In Sarnen und Umgebung finden regelmässig Kurse statt, die von Hatha bis Yin verschiedene Stile abdecken."
    ],
    "nidwalden": [
        "Nidwalden, am Südufer des Vierwaldstättersees gelegen, ist ein kleines Yoga-Paradies in der Zentralschweiz. Die Ruhe des Kantons und die Nähe zum Wasser schaffen eine besondere Atmosphäre für Yoga und Meditation.",
        "In Stans und Umgebung bieten mehrere Studios und Einzellehrer ein vielfältiges Programm. Besonders beliebt sind sanfte Yoga-Formen und Achtsamkeitskurse — passend zur beschaulichen Natur des Kantons."
    ],
    "glarus": [
        "Der Kanton Glarus, eingebettet zwischen steilen Bergflanken, bietet Yoga in einer spektakulären Alpenkulisse. Die kompakte Grösse des Kantons schafft eine enge Community, in der Yoga-Lehrer ihre Schüler persönlich kennen.",
        "In der Hauptstadt Glarus und den umliegenden Gemeinden finden regelmässig Yoga-Kurse statt. Die Nähe zur Natur inspiriert viele Lehrer, Outdoor-Elemente in ihre Praxis zu integrieren — von Bergmeditation bis zu Yoga am Klöntalersee."
    ],
    "zug": [
        "Der Kanton Zug, bekannt als internationaler Wirtschaftsstandort, bietet eine überraschend vielfältige Yoga-Szene. Die kosmopolitische Bevölkerung hat zu einem Angebot beigetragen, das verschiedene Stile und Sprachen abdeckt.",
        "In der Stadt Zug und am Zugersee finden sich Studios, die von kraftvollem Vinyasa bis zu entspannendem Yin Yoga alles anbieten. Viele Kurse werden auf Deutsch und Englisch unterrichtet, was die internationale Community widerspiegelt."
    ],
    "fribourg": [
        "Der zweisprachige Kanton Freiburg vereint deutsche und französische Kultur — und das spiegelt sich auch in der Yoga-Szene wider. In der mittelalterlichen Altstadt von Fribourg und den umliegenden Gemeinden finden sich Studios, die Kurse in beiden Sprachen anbieten.",
        "Die Universität und die junge Bevölkerung sorgen für eine dynamische Yoga-Community. Von traditionellem Hatha über Vinyasa bis zu Aerial Yoga — Freiburg bietet für jeden Geschmack etwas. Die malerische Landschaft mit den Freiburger Voralpen lädt zudem zu Outdoor-Yoga ein."
    ],
    "solothurn": [
        "Solothurn, die schönste Barockstadt der Schweiz, überrascht mit einem vielfältigen Yoga-Angebot. Die historische Altstadt und die Aare bilden eine charmante Kulisse für Yoga-Studios, die Tradition und Moderne verbinden.",
        "Mit rund acht Studios bietet der Kanton ein breites Spektrum an Stilen. Von Olten bis Solothurn Stadt finden Yoga-Begeisterte Kurse für alle Niveaus — von der Einsteiger-Klasse bis zum fortgeschrittenen Workshop."
    ],
    "basel-landschaft": [
        "Basel-Landschaft, der grüne Gürtel um die Stadt Basel, bietet Yoga in einer entspannten Vorstadtatmosphäre. Die gute Anbindung an Basel Stadt kombiniert mit der Nähe zur Natur macht den Kanton attraktiv für Yoga-Praktizierende.",
        "In Liestal, Binningen, Reinach, Muttenz und weiteren Gemeinden finden sich Studios mit einem vielfältigen Angebot. Viele Lehrer haben Verbindungen zur lebendigen Basler Yoga-Szene und bringen internationale Impulse in die Region."
    ],
    "schaffhausen": [
        "Schaffhausen, die Stadt am Rheinfall, bietet Yoga mit Charakter. Die nördlichste Stadt der Schweiz überrascht mit engagierten Studios und einer wachsenden Yoga-Community. Die historische Altstadt und der Munot bilden eine einzigartige Kulisse.",
        "Die Yoga-Studios in Schaffhausen legen Wert auf Qualität und persönliche Betreuung. Ob Hatha, Vinyasa oder Yin — hier wird Yoga in familiärer Atmosphäre praktiziert. Die Nähe zum Bodensee und zum Rhein inspiriert zu einer naturverbundenen Praxis."
    ],
    "appenzell-ar": [
        "Appenzell Ausserrhoden, eingebettet in die sanften Hügel des Alpsteins, bietet Yoga in einer traditionellen und gleichzeitig offenen Umgebung. Die Hauptstadt Herisau und die umliegenden Gemeinden verfügen über ein kompaktes, aber feines Yoga-Angebot.",
        "Die ländliche Idylle und die Nähe zur Natur machen Yoga in Appenzell Ausserrhoden zu einem besonderen Erlebnis. Die Studios hier setzen auf Qualität statt Quantität und bieten eine persönliche Betreuung, die man in grösseren Städten selten findet."
    ],
    "appenzell-ir": [
        "Appenzell Innerrhoden, der kleinste Kanton der Schweiz, überrascht mit einem engagierten Yoga-Angebot. In der malerischen Hauptstadt Appenzell und Umgebung finden Yoga-Begeisterte Kurse, die Tradition und Achtsamkeit verbinden.",
        "Die einzigartige Kulturlandschaft des Alpsteins mit dem Säntis als Wahrzeichen bildet eine inspirierende Kulisse für die Yoga-Praxis. Die Studios hier bieten eine intime Atmosphäre und legen Wert auf ganzheitliche Gesundheitsansätze."
    ],
    "st-gallen": [
        "St. Gallen, die Kulturstadt am Bodensee, bietet eine vielfältige Yoga-Szene. Die UNESCO-Welterbe-Stiftsbibliothek und die lebendige Textiltradition prägen das kulturelle Umfeld, in dem auch Yoga gedeiht. Die Stadt und der gleichnamige Kanton bieten ein breites Spektrum an Studios und Stilen.",
        "Von der Hauptstadt St. Gallen über Rapperswil-Jona bis nach Wil — im ganzen Kanton finden sich Yoga-Angebote. Besonders beliebt sind Vinyasa, Hatha und Yin Yoga. Die Nähe zum Bodensee und zu den Appenzeller Alpen ermöglicht einzigartige Outdoor-Yoga-Erlebnisse."
    ],
    "graubuenden": [
        "Graubünden, der grösste Kanton der Schweiz, bietet Yoga in einer der spektakulärsten Berglandschaften Europas. Von Chur, der ältesten Stadt der Schweiz, über die mondänen Kurorte Davos und St. Moritz bis zu den ruhigen Tälern — Yoga findet hier in einzigartigen Settings statt.",
        "Die Dreisprachigkeit des Kantons (Deutsch, Romanisch, Italienisch) spiegelt sich in der kulturellen Vielfalt der Yoga-Angebote wider. Besonders beliebt sind Yoga-Retreats in den Bergen, die Praxis mit Wandern und Wellness verbinden. Die klare Bergluft und die majestätische Natur machen jede Yoga-Stunde zu einem besonderen Erlebnis."
    ],
    "aargau": [
        "Der Kanton Aargau, zentral zwischen Zürich, Basel und Bern gelegen, bietet ein vielfältiges Yoga-Angebot mit guter Erreichbarkeit. In Aarau, Baden, Wettingen, Brugg und weiteren Gemeinden finden sich Studios für jeden Geschmack und jedes Niveau.",
        "Die Aargauer Yoga-Szene zeichnet sich durch ein gutes Preis-Leistungs-Verhältnis und engagierte Lehrer aus. Von klassischem Hatha über Power Yoga bis zu Prenatal-Kursen — der Kanton bietet alles, was das Yoga-Herz begehrt. Die Nähe zur Natur an Aare und Reuss ermöglicht zudem wunderbare Outdoor-Yoga-Erlebnisse."
    ],
    "thurgau": [
        "Der Kanton Thurgau am Bodensee bietet Yoga in einer malerischen Landschaft zwischen See und sanften Hügeln. In Frauenfeld, Kreuzlingen, Weinfelden und weiteren Gemeinden finden sich engagierte Studios mit einem breiten Angebot.",
        "Die Nähe zum Bodensee macht Yoga im Thurgau besonders reizvoll. Im Sommer locken Outdoor-Sessions am Seeufer, und die ruhige Atmosphäre des Kantons fördert eine achtsame und entspannte Praxis. Von Vinyasa bis Yin — die Thurgauer Studios bieten Vielfalt in familiärer Umgebung."
    ],
    "ticino": [
        "Das Tessin, die Sonnenstube der Schweiz, verbindet italienische Lebensfreude mit einer wachsenden Yoga-Szene. In Lugano, Bellinzona, Locarno und Ascona finden sich Studios, die Yoga mit mediterranem Flair anbieten. Die milde Klimat und die palmengesäumten Seepromenaden schaffen eine besondere Atmosphäre.",
        "Die Yoga-Kultur im Tessin ist stark von der italienischen Tradition beeinflusst. Viele Kurse werden auf Italienisch unterrichtet, einige auch auf Deutsch und Englisch. Besonders beliebt sind Yoga-Retreats am Lago Maggiore und Luganer See. Ascona hat sich als Zentrum für alternative Heilmethoden und Yoga einen Namen gemacht."
    ],
    "valais": [
        "Das Wallis, der sonnigste Kanton der Schweiz, bietet Yoga zwischen Viertausendern und Weinbergen. In Sion, Visp, Brig und Sierre finden sich Studios, die Yoga mit der einzigartigen alpinen Landschaft verbinden.",
        "Die Zweisprachigkeit (Deutsch/Französisch) des Kantons spiegelt sich im Yoga-Angebot wider. Besonders beliebt sind Yoga-Retreats in den Walliser Bergen, die Praxis mit Wandern und Wellness kombinieren. Die reine Bergluft und die majestätischen Gipfel machen jede Yoga-Session zu einem unvergesslichen Erlebnis."
    ],
    "neuchatel": [
        "Der Kanton Neuenburg am gleichnamigen See bietet eine charmante Yoga-Szene in französischsprachiger Umgebung. In der Stadt Neuchâtel und den umliegenden Gemeinden finden sich Studios, die von Hatha über Vinyasa bis zu Yoga Nidra verschiedene Stile anbieten.",
        "Die Lage am Neuenburgersee und die Nähe zum Jura schaffen eine ruhige, inspirierende Umgebung für die Yoga-Praxis. Die Szene ist intim und persönlich — hier kennt man sich und praktiziert gemeinsam. Besonders reizvoll sind Yoga-Sessions mit Blick auf den See und die Alpen."
    ],
    "jura": [
        "Der Kanton Jura, der jüngste Kanton der Schweiz, bietet Yoga in einer unberührten Naturlandschaft. In Delémont und Umgebung finden sich engagierte Yoga-Lehrer, die ein qualitativ hochwertiges Angebot aufgebaut haben.",
        "Die Ruhe und Weite der jurassischen Landschaft bilden eine perfekte Kulisse für eine achtsame Yoga-Praxis. Die Studios hier setzen auf persönliche Betreuung und bieten Kurse hauptsächlich auf Französisch an. Die Nähe zur Natur und die entspannte Atmosphäre machen Yoga im Jura zu einem besonderen Erlebnis."
    ],
}

# Day ordering for schedule tables
DAY_ORDER = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}
DAY_GERMAN = {
    "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag",
    "Sunday": "Sonntag"
}


def escape(text):
    """HTML-escape a string."""
    if text is None:
        return ""
    return html.escape(str(text))


def collect_styles(studios):
    """Collect all unique yoga styles from studios."""
    styles = set()
    for s in studios:
        for st in s.get("styles", []):
            styles.add(st)
    return sorted(styles)


def collect_cities(studios):
    """Collect unique cities from studio addresses."""
    cities = set()
    for s in studios:
        for addr in s.get("addresses", []):
            city = addr.get("city", "").strip()
            if city:
                cities.add(city)
    return sorted(cities)


def generate_studio_cards(studios):
    """Generate HTML cards for studios."""
    if not studios:
        return '<p class="no-data">Keine Studios gefunden. Daten werden laufend aktualisiert.</p>'

    cards = []
    for studio in studios:
        name = escape(studio.get("name", "Unbekannt"))
        website = studio.get("website", "")
        phone = studio.get("phone", "")
        email = studio.get("email", "")
        description = escape(studio.get("description", ""))
        styles = studio.get("styles", [])
        languages = studio.get("languages", [])
        features = studio.get("special_features", [])
        drop_in = studio.get("drop_in", False)
        addresses = studio.get("addresses", [])

        # Build address HTML
        addr_html = ""
        for addr in addresses:
            parts = []
            street = addr.get("street", "").strip()
            if street:
                parts.append(escape(street))
            zip_code = addr.get("zip", "").strip()
            city = addr.get("city", "").strip()
            if zip_code or city:
                parts.append(f"{escape(zip_code)} {escape(city)}".strip())
            label = addr.get("label", "").strip()
            if parts:
                label_html = f' <span class="addr-label">({escape(label)})</span>' if label else ""
                addr_html += f'<p class="studio-address">{", ".join(parts)}{label_html}</p>'

        # Styles badges
        styles_html = ""
        if styles:
            badges = "".join(f'<span class="style-badge">{escape(s)}</span>' for s in styles)
            styles_html = f'<div class="studio-styles">{badges}</div>'

        # Contact links
        contact_html = ""
        contact_parts = []
        if website:
            booking_platforms = ['eversports.', 'classpass.', 'mindbody', 'momoyoga.', 'fitogram.']
            rel_val = 'sponsored noopener noreferrer' if any(bp in website for bp in booking_platforms) else 'nofollow noopener noreferrer'
            contact_parts.append(f'<a href="{escape(website)}" target="_blank" rel="{rel_val}" class="studio-link">Website</a>')
        if phone:
            contact_parts.append(f'<a href="tel:{escape(phone)}" class="studio-link">{escape(phone)}</a>')
        if email:
            contact_parts.append(f'<a href="mailto:{escape(email)}" class="studio-link">{escape(email)}</a>')
        if contact_parts:
            contact_html = f'<div class="studio-contact">{" &middot; ".join(contact_parts)}</div>'

        # Languages
        lang_html = ""
        if languages:
            lang_html = f'<p class="studio-languages">Sprachen: {", ".join(escape(l) for l in languages)}</p>'

        # Features
        features_html = ""
        if features:
            feat_badges = "".join(f'<span class="feature-badge">{escape(f)}</span>' for f in features)
            features_html = f'<div class="studio-features">{feat_badges}</div>'

        # Drop-in badge
        dropin_html = '<span class="dropin-badge">Drop-in</span>' if drop_in else ""

        card = f'''<div class="studio-card">
    <div class="studio-card-header">
        <h3 class="studio-name">{name}{dropin_html}</h3>
    </div>
    {addr_html}
    {description and f'<p class="studio-desc">{description}</p>' or ''}
    {styles_html}
    {contact_html}
    {lang_html}
    {features_html}
</div>'''
        cards.append(card)

    return "\n".join(cards)


def generate_schedule_table(classes):
    """Generate HTML schedule table grouped by day."""
    if not classes:
        return '<p class="no-data">Kein Stundenplan verfügbar. Daten werden laufend aktualisiert.</p>'

    # Sort by day order, then time
    sorted_classes = sorted(classes, key=lambda c: (
        DAY_ORDER.get(c.get("day", "Monday"), 99),
        c.get("time_start", "00:00")
    ))

    # Group by day
    days = OrderedDict()
    for c in sorted_classes:
        day = c.get("day", "Unknown")
        if day not in days:
            days[day] = []
        days[day].append(c)

    rows = []
    for day, day_classes in days.items():
        day_de = DAY_GERMAN.get(day, day)
        rows.append(f'<tr class="day-header"><td colspan="6"><strong>{escape(day_de)}</strong></td></tr>')
        for c in day_classes:
            time_str = f'{escape(c.get("time_start", ""))} - {escape(c.get("time_end", ""))}'
            rows.append(f'''<tr>
    <td class="schedule-day-cell">{escape(day_de)}</td>
    <td class="schedule-time">{time_str}</td>
    <td>{escape(c.get("class_name", ""))}</td>
    <td>{escape(c.get("studio_name", ""))}</td>
    <td>{escape(c.get("teacher", ""))}</td>
    <td>{escape(c.get("level", ""))}</td>
</tr>''')

    return f'''<div class="schedule-table-wrapper">
<table class="schedule-table">
    <thead>
        <tr>
            <th>Tag</th>
            <th>Zeit</th>
            <th>Kurs</th>
            <th>Studio</th>
            <th>Lehrer/in</th>
            <th>Level</th>
        </tr>
    </thead>
    <tbody>
        {"".join(rows)}
    </tbody>
</table>
</div>'''


def generate_other_cantons_links(all_cantons, current_id):
    """Generate internal links to other canton pages."""
    links = []
    for c in all_cantons:
        cid = c["id"]
        if cid == current_id:
            continue
        name = escape(c["name"]["de"])
        abbr = escape(c["abbreviation"])
        links.append(f'<a href="../{cid}/" class="canton-link">{name} ({abbr})</a>')
    return "\n".join(links)


def generate_schema_local_business(studios):
    """Generate Schema.org LocalBusiness JSON-LD for each studio."""
    businesses = []
    for studio in studios:
        name = studio.get("name", "")
        website = studio.get("website", "")
        phone = studio.get("phone", "")
        addresses = studio.get("addresses", [])
        lat = studio.get("lat")
        lng = studio.get("lng")
        hours = studio.get("hours", "")

        if not addresses:
            continue

        addr = addresses[0]
        biz = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": name,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": addr.get("street", ""),
                "postalCode": addr.get("zip", ""),
                "addressLocality": addr.get("city", ""),
                "addressCountry": "CH"
            }
        }
        if website:
            biz["url"] = website
        if phone:
            biz["telephone"] = phone
        if lat and lng:
            biz["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": lat,
                "longitude": lng
            }
        if hours:
            biz["openingHours"] = hours

        pricing = studio.get("pricing", {})
        if isinstance(pricing, dict) and pricing.get("single"):
            single = pricing["single"]
            cur = pricing.get("currency", "CHF")
            biz["priceRange"] = f"{cur} {single} (Einzellektion)"

        businesses.append(biz)
    return businesses


def generate_faq_schema(canton_name, canton_abbr, num_studios, num_classes, styles, cities, studios):
    """Generate FAQPage schema with location-specific Q&A."""
    # Compute price range from studios with pricing
    prices = [s["pricing"]["single"] for s in studios
              if isinstance(s.get("pricing"), dict) and s["pricing"].get("single")
              and isinstance(s["pricing"]["single"], (int, float)) and s["pricing"]["single"] < 100]
    price_info = ""
    if prices:
        price_info = f" Die Preise für eine Einzellektion liegen zwischen CHF {min(prices)} und CHF {max(prices)}."

    top_styles = ", ".join(styles[:5]) if styles else "diverse Stile"
    top_cities = ", ".join(cities[:4]) if cities else canton_name

    faqs = [
        {
            "q": f"Wie viele Yoga-Studios gibt es im Kanton {canton_name}?",
            "a": f"Im Kanton {canton_name} ({canton_abbr}) sind aktuell {num_studios} Yoga-Studios mit insgesamt {num_classes} wöchentlichen Kursen gelistet. Diese Daten werden wöchentlich aktualisiert."
        },
        {
            "q": f"Welche Yoga-Stile werden in {canton_name} angeboten?",
            "a": f"Die Studios in {canton_name} bieten unter anderem folgende Stile an: {top_styles}. Insgesamt sind {len(styles)} verschiedene Yoga-Stile vertreten."
        },
        {
            "q": f"Was kostet eine Yoga-Stunde in {canton_name}?",
            "a": f"Die Preise variieren je nach Studio und Angebot.{price_info} Viele Studios bieten Probeangebote, 10er-Karten und Monatsabos an."
        },
        {
            "q": f"In welchen Städten gibt es Yoga-Studios im Kanton {canton_name}?",
            "a": f"Yoga-Studios finden Sie u.a. in {top_cities}. Alle Standorte mit Adressen und Kontaktdaten sind auf dieser Seite aufgelistet."
        }
    ]

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["q"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["a"]
                }
            }
            for faq in faqs
        ]
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


DAY_TO_SCHEMA = {
    "Monday": "https://schema.org/Monday",
    "Tuesday": "https://schema.org/Tuesday",
    "Wednesday": "https://schema.org/Wednesday",
    "Thursday": "https://schema.org/Thursday",
    "Friday": "https://schema.org/Friday",
    "Saturday": "https://schema.org/Saturday",
    "Sunday": "https://schema.org/Sunday"
}


def generate_event_schema(classes, studios, canton_name):
    """Generate Event schema for recurring yoga classes (max 25 per canton)."""
    if not classes:
        return ""

    studio_map = {s["id"]: s for s in studios}
    events = []

    # Pick up to 25 diverse classes (spread across studios)
    selected = classes[:25]

    for c in selected:
        studio = studio_map.get(c.get("studio_id"), {})
        addr = studio.get("addresses", [{}])[0] if studio.get("addresses") else {}
        day = c.get("day", "Monday")

        event = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": c.get("class_name", "Yoga"),
            "description": f'{c.get("class_name", "Yoga")} bei {c.get("studio_name", "")} in {canton_name}',
            "eventSchedule": {
                "@type": "Schedule",
                "byDay": DAY_TO_SCHEMA.get(day, day),
                "startTime": c.get("time_start", ""),
                "endTime": c.get("time_end", ""),
                "repeatFrequency": "P1W"
            },
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "location": {
                "@type": "Place",
                "name": c.get("studio_name", ""),
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": addr.get("street", ""),
                    "postalCode": addr.get("zip", ""),
                    "addressLocality": addr.get("city", ""),
                    "addressCountry": "CH"
                }
            },
            "organizer": {
                "@type": "Organization",
                "name": c.get("studio_name", ""),
            }
        }

        if studio.get("website"):
            event["url"] = studio["website"]
            event["organizer"]["url"] = studio["website"]

        if c.get("teacher"):
            event["performer"] = {"@type": "Person", "name": c["teacher"]}

        pricing = studio.get("pricing", {})
        if isinstance(pricing, dict) and pricing.get("single"):
            event["offers"] = {
                "@type": "Offer",
                "price": str(pricing["single"]),
                "priceCurrency": pricing.get("currency", "CHF"),
                "availability": "https://schema.org/InStock",
                "validFrom": "2026-01-01"
            }

        events.append(event)

    scripts = ""
    for ev in events:
        scripts += f'\n    <script type="application/ld+json">\n    {json.dumps(ev, ensure_ascii=False, indent=2)}\n    </script>'
    return scripts


def generate_page(canton, studios, classes, all_cantons):
    """Generate the full HTML page for a canton."""
    canton_id = canton["id"]
    canton_name = canton["name"]["de"]
    canton_abbr = canton["abbreviation"]
    canton_capital = canton.get("capital", "")

    num_studios = len(studios)
    num_classes = len(classes)
    all_styles = collect_styles(studios)
    num_styles = len(all_styles)
    cities = collect_cities(studios)
    cities_str = ", ".join(cities[:5])  # top 5 cities for meta
    styles_str = ", ".join(all_styles[:8])  # top 8 styles for meta

    # Descriptions
    desc_paragraphs = CANTON_DESCRIPTIONS.get(canton_id, [
        f"Der Kanton {canton_name} bietet ein vielfältiges Yoga-Angebot. In {canton_capital} und Umgebung finden Yoga-Begeisterte Studios und Kurse für verschiedene Stile und Niveaus.",
        f"Die Yoga-Szene in {canton_name} wächst stetig und bietet sowohl für Anfänger als auch für Fortgeschrittene passende Angebote. Entdecken Sie die Studios und Kurse in Ihrer Nähe."
    ])

    # Schema.org
    studio_items = []
    for i, s in enumerate(studios, 1):
        item = {"@type": "ListItem", "position": i, "name": s.get("name", "")}
        if s.get("website"):
            item["url"] = s["website"]
        studio_items.append(item)

    schema_itemlist = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Yoga Studios im Kanton {canton_name}",
        "numberOfItems": num_studios,
        "itemListElement": studio_items
    }, ensure_ascii=False, indent=2)

    schema_breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Kantone", "item": f"{BASE_URL}/kanton/"},
            {"@type": "ListItem", "position": 3, "name": canton_name, "item": f"{BASE_URL}/kanton/{canton_id}/"}
        ]
    }, ensure_ascii=False, indent=2)

    from datetime import date
    schema_webpage = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"Yoga in {canton_name}",
        "description": f"Alle {num_studios} Yoga-Studios im Kanton {canton_name} ({canton_abbr}). Stundenplan, Adressen und Kontaktdaten.",
        "url": f"{BASE_URL}/kanton/{canton_id}/",
        "isPartOf": {"@type": "WebSite", "url": f"{BASE_URL}/"},
        "inLanguage": "de",
        "dateModified": date.today().isoformat(),
        "about": {
            "@type": "Thing",
            "name": "Yoga",
            "description": f"Yoga-Studios und Kurse im Kanton {canton_name}, Schweiz"
        }
    }, ensure_ascii=False, indent=2)

    local_businesses = generate_schema_local_business(studios)
    local_biz_scripts = ""
    for biz in local_businesses:
        local_biz_scripts += f'\n    <script type="application/ld+json">\n    {json.dumps(biz, ensure_ascii=False, indent=2)}\n    </script>'

    schema_faq = generate_faq_schema(canton_name, canton_abbr, num_studios, num_classes, all_styles, cities, studios)
    event_scripts = generate_event_schema(classes, studios, canton_name)

    # Content sections
    studio_cards_html = generate_studio_cards(studios)
    schedule_html = generate_schedule_table(classes)
    other_cantons_html = generate_other_cantons_links(all_cantons, canton_id)

    # Related content links — style pages + blog posts
    city_slug_map = {
        "Basel": "basel", "Zürich": "zuerich", "Bern": "bern",
        "Genf": "genf", "Genève": "genf", "Lausanne": "lausanne", "Luzern": "luzern"
    }
    style_slug_map = {
        "Vinyasa": "vinyasa", "Hatha": "hatha", "Yin": "yin", "Ashtanga": "ashtanga",
        "Hot": "hot", "Aerial": "aerial", "Kundalini": "kundalini", "Power": "power",
        "Restorative": "restorative", "Schwangerschaftsyoga": "schwangerschafts"
    }
    main_city = cities[0] if cities else ""
    city_slug = city_slug_map.get(main_city, "")
    style_links = []
    if city_slug:
        for style in all_styles[:6]:
            slug = style_slug_map.get(style, "")
            if slug:
                style_links.append(f'<a href="../../yoga/{slug}-yoga-{city_slug}/">{escape(style)} Yoga {escape(main_city)}</a>')

    blog_links = [
        '<a href="../../blog/yoga-fuer-anfaenger/">Yoga für Anfänger — Der komplette Guide</a>',
        '<a href="../../blog/yoga-stile-vergleich/">Alle Yoga-Stile im Vergleich</a>',
        '<a href="../../blog/yoga-preise-schweiz-2026/">Yoga-Preise Schweiz 2026</a>',
    ]
    if canton_id == "basel-stadt" or canton_id == "basel-landschaft":
        blog_links.insert(0, '<a href="../../blog/beste-yoga-studios-basel-2026/">Die 15 besten Yoga-Studios in Basel</a>')
    elif canton_id == "zurich":
        blog_links.insert(0, '<a href="../../blog/beste-yoga-studios-zuerich-2026/">Die besten Yoga-Studios in Zürich</a>')

    related_html = ""
    if style_links or blog_links:
        items = ""
        for sl in style_links:
            items += f'<li>{sl}</li>\n'
        for bl in blog_links:
            items += f'<li>{bl}</li>\n'
        related_html = f'''<section class="related-content">
    <div class="canton-container">
        <h2>Weiterführende Artikel</h2>
        <ul class="related-links">{items}</ul>
    </div>
</section>'''

    # Description paragraphs
    desc_html = "\n".join(f'<p>{escape(p)}</p>' for p in desc_paragraphs)

    # Stats section
    stats_html = f'''<div class="canton-stats">
    <div class="stat-item">
        <span class="stat-number">{num_studios}</span>
        <span class="stat-label">Studios</span>
    </div>
    <div class="stat-item">
        <span class="stat-number">{num_classes}</span>
        <span class="stat-label">Kurse/Woche</span>
    </div>
    <div class="stat-item">
        <span class="stat-number">{num_styles}</span>
        <span class="stat-label">Yoga-Stile</span>
    </div>
</div>'''

    meta_desc_full = f"Yoga im Kanton {canton_name} ({canton_abbr}): {num_studios} Studios, {num_classes} Kurse pro Woche. {cities_str}. Stile: {styles_str}. Stundenplan & Kontaktdaten."
    # Limit meta description to 150 chars (pre-escape) to stay under 160 after HTML escaping
    if len(meta_desc_full) > 150:
        meta_desc = meta_desc_full[:147].rsplit(' ', 1)[0] + '...'
    else:
        meta_desc = meta_desc_full
    meta_keywords = f"Yoga {canton_name}, Yoga {canton_abbr}, Yoga {canton_capital}, Yoga Studio {canton_name}, Yoga Kurse {canton_name}, {', '.join(f'Yoga {c}' for c in cities[:5])}, {', '.join(all_styles[:6])}, Yoga Schweiz"

    page = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yoga in {escape(canton_name)} 2026 — {num_studios} Studios, Kurse &amp; Stundenplan | Yoga Schweiz</title>
    <meta name="description" content="{escape(meta_desc)}">
    <meta name="keywords" content="{escape(meta_keywords)}">
    <meta name="author" content="YogaSchweiz">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{BASE_URL}/kanton/{canton_id}/">

    <!-- Hreflang -->
    <link rel="alternate" hreflang="de" href="{BASE_URL}/kanton/{canton_id}/">
    <link rel="alternate" hreflang="en" href="{BASE_URL}/kanton/{canton_id}/?lang=en">
    <link rel="alternate" hreflang="it" href="{BASE_URL}/kanton/{canton_id}/?lang=it">
    <link rel="alternate" hreflang="fr" href="{BASE_URL}/kanton/{canton_id}/?lang=fr">
    <link rel="alternate" hreflang="x-default" href="{BASE_URL}/kanton/{canton_id}/">

    <!-- Open Graph -->
    <meta property="og:title" content="Yoga in {escape(canton_name)} 2026 — {num_studios} Studios &amp; Stundenplan">
    <meta property="og:description" content="{escape(meta_desc)}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{BASE_URL}/kanton/{canton_id}/">
    <meta property="og:locale" content="de_CH">
    <meta property="og:site_name" content="Yoga Schweiz">
    <meta property="og:image" content="{BASE_URL}/img/og-image.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Yoga in {escape(canton_name)} — {num_studios} Studios">
    <meta name="twitter:description" content="{escape(meta_desc)}">

    <!-- Schema.org WebPage -->
    <script type="application/ld+json">
    {schema_webpage}
    </script>
    <!-- Schema.org BreadcrumbList -->
    <script type="application/ld+json">
    {schema_breadcrumb}
    </script>
    <!-- Schema.org ItemList -->
    <script type="application/ld+json">
    {schema_itemlist}
    </script>
    <!-- Schema.org LocalBusiness (per studio) -->{local_biz_scripts}
    <!-- Schema.org FAQPage -->
    <script type="application/ld+json">
    {schema_faq}
    </script>
    <!-- Schema.org Events (recurring yoga classes) -->{event_scripts}

    <!-- Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧘</text></svg>">

    <!-- Fonts (self-hosted) -->
    <link rel="stylesheet" href="../../css/fonts.css">

    <!-- Main site CSS -->
    <link rel="stylesheet" href="../../css/style.css">

    <!-- Canton page specific styles -->
    <style>
        .canton-hero {{
            background: linear-gradient(135deg, #6B5B95 0%, #8B7DB5 40%, #D4A373 100%);
            color: #fff;
            padding: 80px 0 60px;
            text-align: center;
        }}
        .canton-hero h1 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.8rem;
            margin-bottom: 8px;
            font-weight: 700;
        }}
        .canton-hero .canton-subtitle {{
            font-size: 1.15rem;
            opacity: 0.92;
            margin-bottom: 24px;
        }}
        .canton-stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            margin-top: 20px;
        }}
        .stat-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .stat-number {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1;
        }}
        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.85;
            margin-top: 4px;
        }}
        .canton-container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        .canton-section {{
            padding: 48px 0;
        }}
        .canton-section h2 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.9rem;
            color: #6B5B95;
            margin-bottom: 24px;
            border-bottom: 2px solid #D4A373;
            padding-bottom: 8px;
        }}
        .canton-description p {{
            font-size: 1.05rem;
            line-height: 1.75;
            color: #444;
            margin-bottom: 16px;
            max-width: 800px;
        }}
        .studio-card {{
            background: #fff;
            border: 1px solid #E8E8E8;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: box-shadow 0.25s ease, transform 0.25s ease;
        }}
        .studio-card:hover {{
            box-shadow: 0 6px 20px rgba(107,91,149,0.12);
            transform: translateY(-2px);
        }}
        .studio-card-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }}
        .studio-name {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.3rem;
            color: #2D2D2D;
            margin: 0;
        }}
        .studio-address {{
            font-size: 0.92rem;
            color: #666;
            margin-bottom: 4px;
        }}
        .addr-label {{
            font-size: 0.82rem;
            color: #999;
        }}
        .studio-desc {{
            font-size: 0.95rem;
            color: #555;
            margin: 10px 0;
            line-height: 1.6;
        }}
        .studio-styles {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 12px 0;
        }}
        .style-badge {{
            background: #F3F0F8;
            color: #6B5B95;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        .studio-contact {{
            margin: 10px 0;
            font-size: 0.9rem;
        }}
        .studio-link {{
            color: #6B5B95;
            text-decoration: none;
            font-weight: 500;
        }}
        .studio-link:hover {{
            color: #D4A373;
            text-decoration: underline;
        }}
        .studio-languages {{
            font-size: 0.88rem;
            color: #777;
            margin: 6px 0;
        }}
        .studio-features {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }}
        .feature-badge {{
            background: #FFF8F0;
            color: #D4A373;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 500;
            border: 1px solid #E8C9A4;
        }}
        .dropin-badge {{
            background: #4CAF50;
            color: #fff;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 10px;
            vertical-align: middle;
        }}
        .no-data {{
            color: #999;
            font-style: italic;
            padding: 20px 0;
        }}
        .schedule-table-wrapper {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        .schedule-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        .schedule-table th {{
            background: #6B5B95;
            color: #fff;
            padding: 10px 14px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        .schedule-table td {{
            padding: 8px 14px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        .schedule-table tr:hover td {{
            background: #F3F0F8;
        }}
        .day-header td {{
            background: #F8F6FC;
            padding: 12px 14px;
            font-size: 0.95rem;
        }}
        .schedule-day-cell {{
            display: none;
        }}
        .schedule-time {{
            white-space: nowrap;
            font-weight: 500;
            color: #6B5B95;
        }}
        .related-content {{
            padding: 40px 0;
            border-top: 2px solid #E8E8E8;
        }}
        .related-content h2 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.4rem;
            color: #6B5B95;
            margin-bottom: 16px;
        }}
        .related-links {{
            list-style: none;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .related-links li {{
            background: #F3F0F8;
            border-radius: 8px;
        }}
        .related-links a {{
            display: block;
            padding: 8px 16px;
            color: #6B5B95;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        .related-links a:hover {{
            background: #6B5B95;
            color: #fff;
            border-radius: 8px;
        }}
        .other-cantons {{
            background: #F8F6FC;
            padding: 48px 0;
        }}
        .other-cantons h2 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.6rem;
            color: #6B5B95;
            margin-bottom: 20px;
            text-align: center;
        }}
        .canton-links {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}
        .canton-link {{
            background: #fff;
            color: #6B5B95;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.88rem;
            font-weight: 500;
            border: 1px solid #E8E8E8;
            transition: all 0.2s ease;
        }}
        .canton-link:hover {{
            background: #6B5B95;
            color: #fff;
            border-color: #6B5B95;
        }}
        .canton-breadcrumb {{
            font-size: 0.85rem;
            padding: 16px 0;
            color: #777;
        }}
        .canton-breadcrumb a {{
            color: #6B5B95;
            text-decoration: none;
        }}
        .canton-breadcrumb a:hover {{
            text-decoration: underline;
        }}
        .canton-header {{
            background: #fff;
            border-bottom: 1px solid #E8E8E8;
            padding: 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .canton-header-inner {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 14px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .canton-logo {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.3rem;
            color: #6B5B95;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .canton-logo strong {{
            color: #D4A373;
        }}
        .canton-nav {{
            display: flex;
            gap: 20px;
            list-style: none;
        }}
        .canton-nav a {{
            color: #555;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: color 0.2s;
        }}
        .canton-nav a:hover {{
            color: #6B5B95;
        }}
        .canton-footer {{
            background: #2D2D2D;
            color: #aaa;
            padding: 32px 0;
            text-align: center;
            font-size: 0.85rem;
        }}
        .canton-footer a {{
            color: #D4A373;
            text-decoration: none;
        }}
        .canton-footer a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 768px) {{
            .canton-hero h1 {{ font-size: 1.8rem; }}
            .canton-stats {{ gap: 24px; }}
            .stat-number {{ font-size: 1.6rem; }}
            .canton-section h2 {{ font-size: 1.4rem; }}
            .canton-nav {{ gap: 12px; }}
            .canton-nav a {{ font-size: 0.8rem; }}
            .studio-card {{ padding: 16px; }}
            .canton-header-inner {{ flex-direction: column; gap: 10px; }}
        }}
        @media (max-width: 480px) {{
            .canton-hero {{ padding: 60px 0 40px; }}
            .canton-hero h1 {{ font-size: 1.5rem; }}
            .canton-stats {{ flex-direction: column; gap: 16px; }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="canton-header">
        <div class="canton-header-inner">
            <a href="../../" class="canton-logo">
                <span>🧘</span>
                <span>Yoga<strong>Schweiz</strong></span>
            </a>
            <nav>
                <ul class="canton-nav">
                    <li><a href="../../">Home</a></li>
                    <li><a href="#studios">Studios</a></li>
                    <li><a href="#stundenplan">Stundenplan</a></li>
                    <li><a href="#andere-kantone">Kantone</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <!-- Breadcrumb -->
    <div class="canton-container">
        <nav class="canton-breadcrumb" aria-label="Breadcrumb">
            <a href="../../">Home</a> &rsaquo;
            Kantone &rsaquo;
            <strong>{escape(canton_name)} ({escape(canton_abbr)})</strong>
        </nav>
    </div>

    <!-- Hero -->
    <section class="canton-hero">
        <div class="canton-container">
            <h1>Yoga in {escape(canton_name)}</h1>
            <p class="canton-subtitle">Kanton {escape(canton_name)} ({escape(canton_abbr)}) — Alle Yoga-Studios und Kurse auf einen Blick</p>
            {stats_html}
        </div>
    </section>

    <!-- Description -->
    <section class="canton-section">
        <div class="canton-container canton-description">
            <h2>Yoga im Kanton {escape(canton_name)}</h2>
            {desc_html}
        </div>
    </section>

    <!-- Studios -->
    <section class="canton-section" id="studios">
        <div class="canton-container">
            <h2>Yoga-Studios in {escape(canton_name)} ({num_studios})</h2>
            {studio_cards_html}
        </div>
    </section>

    <!-- Schedule -->
    <section class="canton-section" id="stundenplan">
        <div class="canton-container">
            <h2>Stundenplan — {escape(canton_name)}</h2>
            <p style="color:#777;margin-bottom:20px;font-size:0.9rem;">{num_classes} Klassen pro Woche</p>
            {schedule_html}
        </div>
    </section>

    {related_html}

    <!-- Other Cantons -->
    <section class="other-cantons" id="andere-kantone">
        <div class="canton-container">
            <h2>Yoga in anderen Kantonen</h2>
            <div class="canton-links">
                {other_cantons_html}
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="canton-footer">
        <div class="canton-container">
            <p>
                <a href="../../">Yoga Schweiz</a> — Alle Yoga-Studios und Kurse der Schweiz
            </p>
            <p style="margin-top:8px;">
                &copy; 2026 YogaSchweiz. Alle Angaben ohne Gewähr. Daten werden regelmässig aktualisiert.
            </p>
            <p style="margin-top:8px;font-size:0.8rem;color:#777;">
                Für aktuelle Kurszeiten und Preise bitte direkt die Studio-Websites besuchen.
            </p>
        </div>
    </footer>
</body>
</html>'''
    return page


def main():
    print("=== Generating canton pages ===")
    print(f"Base directory: {BASE_DIR}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Load all cantons
    cantons = load_cantons()
    if not cantons:
        print("ERROR: No cantons found in cantons.json!")
        return

    print(f"Found {len(cantons)} cantons")

    # Build mapping of available data files
    studio_files = glob.glob(os.path.join(DATA_DIR, "studios_*.json"))
    schedule_files = glob.glob(os.path.join(DATA_DIR, "schedule_*.json"))

    # Extract keys from filenames (exclude .enc.json files)
    available_studio_keys = set()
    for f in studio_files:
        basename = os.path.basename(f)
        if ".enc." in basename:
            continue
        key = basename.replace("studios_", "").replace(".json", "")
        available_studio_keys.add(key)

    available_schedule_keys = set()
    for f in schedule_files:
        basename = os.path.basename(f)
        if ".enc." in basename:
            continue
        key = basename.replace("schedule_", "").replace(".json", "")
        available_schedule_keys.add(key)

    print(f"Available studio data: {len(available_studio_keys)} files")
    print(f"Available schedule data: {len(available_schedule_keys)} files")
    print()

    total_studios = 0
    total_classes = 0

    for canton in cantons:
        canton_id = canton["id"]
        canton_name = canton["name"]["de"]
        file_key = get_file_key(canton_id)

        print(f"Generating: {canton_name} ({canton_id}) ...", end=" ")

        # Load data
        studios = []
        classes = []

        if file_key in available_studio_keys:
            studios = load_studios(file_key)
        else:
            print(f"[no studio file for key '{file_key}']", end=" ")

        if file_key in available_schedule_keys:
            classes = load_schedule(file_key)
        else:
            print(f"[no schedule file for key '{file_key}']", end=" ")

        # Generate HTML
        html_content = generate_page(canton, studios, classes, cantons)

        # Write to file
        output_path = os.path.join(OUTPUT_DIR, canton_id, "index.html")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        total_studios += len(studios)
        total_classes += len(classes)

        print(f"OK ({len(studios)} studios, {len(classes)} classes)")

    print()
    print(f"=== Done! Generated {len(cantons)} canton pages ===")
    print(f"Total studios: {total_studios}")
    print(f"Total classes: {total_classes}")
    print(f"Output: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
