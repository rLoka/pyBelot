import random
import time
import operator
import threading
import time
import string
import pygame
import Tkinter

# zodb
from ZEO import ClientStorage
from ZODB import DB
from ZODB.POSException import ConflictError
from persistent import Persistent
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from tkSimpleDialog import askstring
import transaction

karteSpritesList = []
vidljiveKarteSprites = pygame.sprite.LayeredUpdates()
adutiSprites = pygame.sprite.LayeredUpdates()
adutiObaveznoSprites = pygame.sprite.LayeredUpdates()
sobeSprites = pygame.sprite.Group()

KARTE = [
    {
        'naziv': '7',
        'vrijednost': 0,
        'vrijednostAduta': 0,
        'jacina': 0,
        'poredak': 1,
        'jacinaAduta': 0,
        'oznaka': '7'
    },
    {
        'naziv': '8',
        'vrijednost': 0,
        'vrijednostAduta': 0,
        'jacina': 1,
        'poredak': 2,
        'jacinaAduta': 1,
        'oznaka': '8'
    },
    {
        'naziv': '9',
        'vrijednost': 0,
        'vrijednostAduta': 14,
        'jacina': 2,
        'poredak': 3,
        'jacinaAduta': 6,
        'oznaka': '9'
    },
    {
        'naziv': '10',
        'vrijednost': 10,
        'vrijednostAduta': 10,
        'jacina': 6,
        'poredak': 4,
        'jacinaAduta': 4,
        'oznaka': '1'
    },
    {
        'naziv': 'Decko',
        'vrijednost': 2,
        'vrijednostAduta': 20,
        'jacina': 3,
        'poredak': 5,
        'jacinaAduta': 7,
        'oznaka': 'd'
    },
    {
        'naziv': 'Baba',
        'vrijednost': 3,
        'vrijednostAduta': 3,
        'jacina': 4,
        'poredak': 6,
        'jacinaAduta': 2,
        'oznaka': 'b'
    },
    {
        'naziv': 'Kralj',
        'vrijednost': 4,
        'vrijednostAduta': 4,
        'jacina': 5,
        'poredak': 7,
        'jacinaAduta': 3,
        'oznaka': 'k'
    },
    {
        'naziv': 'As',
        'vrijednost': 11,
        'vrijednostAduta': 11,
        'jacina': 7,
        'poredak': 8,
        'jacinaAduta': 5,
        'oznaka': 'a'
    }
]

BOJE = {
    'Herc': ['h', 'img/herc.png'],
    'Bundeva': ['b', 'img/bundeva.png'],
    'Zelena': ['z', 'img/zelena.png'],
    'Zir': ['r', 'img/zir.png']
}


class Igrac(Persistent):
    def __init__(self, nadimak, jeLiRacunalo, igra):
        self.nadimak = nadimak
        self.karte = PersistentList()
        self.igra = igra
        self.jeLiRacunalo = jeLiRacunalo
        self.zastavice = PersistentDict()

        self.zastavice.update(
            {
                'uzmiKarte': 0,
                'provjeriZvanja': 0,
                'hocuLiZvati': 0,
                'baciKartu': 0
            }
        )

        self.igra.onSudjeluj(self)
        transaction.commit()

    def uzmiKarte(self):
        global vidljiveKarteSprites
        global karteSpritesList
        self.karte.extend(self.igra.onDajKarte())
        self.karte = self.sortirajKarte(self.karte)
        for i in range(len(self.karte)):
            kartaSprite = next((x for x in karteSpritesList if x.karta == self.karte[i]), None)
            kartaSprite.pozicioniraj((1000 - (100 * len(self.karte))) / 2 + 100 * i, 566)
            kartaSprite.layer = i
            kartaSprite.prikazi()
            vidljiveKarteSprites.add(kartaSprite)

    def sortirajKarte(self, karte):
        return sorted(karte, key=lambda karta: (karta.boja, karta.poredak), reverse=False)

    def provjeriZvanja(self):
        self.igra.onPrijaviZvanje(self, self.karte)

    def hocuLiZvati(self, moramLiZvati):
        if self.jeLiRacunalo == True:
            jacinaAduta = {
                'Herc': 0,
                'Bundeva': 0,
                'Zelena': 0,
                'Zir': 0
            }
            for karta in self.karte:
                if karta.boja == 'Herc':
                    jacinaAduta['Herc'] += karta.vrijednostAduta
                elif karta.boja == 'Bundeva':
                    jacinaAduta['Bundeva'] += karta.vrijednostAduta
                elif karta.boja == 'Zelena':
                    jacinaAduta['Zelena'] += karta.vrijednostAduta
                elif karta.boja == 'Zir':
                    jacinaAduta['Zir'] += karta.vrijednostAduta

            najjacaBoja = max(jacinaAduta, key=jacinaAduta.get)

            if jacinaAduta[najjacaBoja] > 30 or moramLiZvati:
                print self.nadimak + ": zovem " + najjacaBoja
                self.igra.onOdaberiAdut(najjacaBoja)
            else:
                print self.nadimak + ": dalje!"
                self.igra.onOdaberiAdut(False)
                return False

    def baciKartu(self, odabranaKarta=None):
        if (self.jeLiRacunalo == True):
            for karta in self.karte:
                if self.igra.onJeLiPoPravilima(self.karte, karta) == True:
                    time.sleep(.01)
                    print self.nadimak + ": ", karta
                    self.karte.remove(karta)
                    self.igra.onBaciKartu(karta)
                else:
                    continue
        else:
            if self.igra.onJeLiPoPravilima(self.karte, odabranaKarta) == True:
                self.zastavice["baciKartu"] = 0
                self.igra.onBaciKartu(self.karte.pop(self.karte.index(odabranaKarta)))
                return True
            else:
                return False


class Igra(Persistent):
    def __init__(self, karte, boje):

        self.karte = karte
        self.boje = boje
        self.spil = Spil(self.karte, self.boje)
        self.runda = Runda()

        self.timovi = PersistentList()
        self.tim1 = Tim()
        self.tim2 = Tim()
        self.redIgraca = PersistentList()

        self.redAduti = PersistentList()
        self.redZvanja = PersistentList()
        self.brojBacanja = 0
        self.redBacanja = PersistentList()

        self.mi = 0
        self.vi = 0
        self.miRunda = 0
        self.viRunda = 0
        transaction.commit()

    def onSudjeluj(self, igrac):
        if len(self.redIgraca) < 4:
            if len(self.tim1.igraci) < 2:
                self.tim1.dodajNovogIgraca(igrac)
            else:
                self.tim2.dodajNovogIgraca(igrac)
            self.redIgraca.append(igrac)
            if len(self.redIgraca) == 4:
                self.originalniRedIgraca = self.redIgraca
                self.timovi.append(self.tim1)
                self.timovi.append(self.tim2)
                self.zapocniNovuRundu()
            transaction.commit()

    def zapocniNovuRundu(self):
        if self.mi < 1001 and self.vi < 1001:
            self.spil.promijesaj()
            self.runda = Runda()
            self.miRunda = 0
            self.viRunda = 0
            self.brojBacanja = 0
            self.redKarte = 0
            self.redAduti = 0
            self.redZvanja = PersistentList()
            self.redBacanja = 0
            self.reciIgracimaDaUzmuKarte()
            transaction.commit()

    def reciIgracimaDaUzmuKarte(self):
        self.redIgraca[self.redKarte].zastavice['uzmiKarte'] = 1

    def onDajKarte(self):
        self.redKarte += 1
        if self.redKarte < 4:
            self.reciIgracimaDaUzmuKarte()
        else:
            self.pitajIgraceZaAdut()
        return self.spil.podijeli()

    def pitajIgraceZaAdut(self):
        if self.redAduti == 0:
            self.redIgraca[0].zastavice['hocuLiZvati'] = 1
        elif self.redAduti == 1:
            self.redIgraca[1].zastavice['hocuLiZvati'] = 1
        elif self.redAduti == 2:
            self.redIgraca[2].zastavice['hocuLiZvati'] = 1
        elif self.redAduti == 3:
            self.redIgraca[3].zastavice['hocuLiZvati'] = 2
        transaction.commit()

    def onOdaberiAdut(self, odluka):
        if odluka != False:
            if self.redIgraca[self.redAduti] in self.timovi[0].igraci:
                self.runda.postaviAdut(odluka, self.timovi[0])
            else:
                self.runda.postaviAdut(odluka, self.timovi[1])
            transaction.commit()
            #self.pitajIgraceZaZvanje()
            self.bacanje = Bacanje()
            self.runda.dodajBacanje(self.bacanje)
            self.traziBacanjeKarte()
            self.traziBacanjeKarte()
        else:
            self.redAduti += 1
            self.pitajIgraceZaAdut()

    def pitajIgraceZaZvanje(self):
        self.redIgraca[len(self.redZvanja)].zastavice['provjeriZvanja'] = 1
        transaction.commit()

    def onPrijaviZvanje(self, igrac, zvanje):
        self.provjeriZvanje(zvanje, igrac)
        if len(self.redZvanja) < 4:
            self.pitajIgraceZaZvanje()
        else:
            self.bacanje = Bacanje()
            self.runda.dodajBacanje(self.bacanje)
            self.traziBacanjeKarte()
            # ovo treba dodatno

    def traziBacanjeKarte(self):
        redoslijed = len(self.runda.bacanja[-1].baceneKarte)
        self.redIgraca[redoslijed].zastavice['baciKartu'] = 1
        transaction.commit()

    def onBaciKartu(self, karta):
        self.runda.bacanja[-1].baceneKarte.append(karta)
        if len(self.runda.bacanja[-1].baceneKarte) < 4:
            self.traziBacanjeKarte()
        else:
            self.nosi()
            if len(self.runda.bacanja) < 8:
                self.bacanje = Bacanje()
                self.runda.dodajBacanje(self.bacanje)
                self.traziBacanjeKarte()
            else:
                self.zavrsiRundu()

    def zavrsiRundu(self):
        if self.runda.timKojiJeZvao == self.timovi[0]:
            if self.miRunda >= self.viRunda:
                self.mi += self.miRunda
                self.vi += self.viRunda
                print self.timovi[0].igraci[0].nadimak + " i " + self.timovi[0].igraci[1].nadimak + "su prosli!"
            else:
                self.mi += 0
                self.vi += self.viRunda + self.miRunda
                print self.timovi[0].igraci[0].nadimak + " i " + self.timovi[0].igraci[1].nadimak + "su pali!"
        else:
            if self.miRunda <= self.viRunda:
                self.mi += self.miRunda
                self.vi += self.viRunda
                print self.timovi[1].igraci[0].nadimak + " i " + self.timovi[1].igraci[1].nadimak + "su prosli!"
            else:
                self.mi += self.viRunda + self.miRunda
                self.vi += 0
                print self.timovi[1].igraci[0].nadimak + " i " + self.timovi[1].igraci[1].nadimak + "su pali!"

        print "Igra mi: " + str(self.mi)
        print "Igra vi: " + str(self.vi)

        self.promijeniRedoslijed(1, self.originalniRedIgraca)
        self.redIgraca = self.originalniRedIgraca
        self.zapocniNovuRundu()
        self.spil = Spil(self.karte, self.boje)
        transaction.commit()

    def onJeLiPoPravilima(self, mojeKarte, kartaKojuZelimOdigrati):
        # ako baca prvi onda moze baciti bilo sto
        if not self.runda.bacanja[-1].baceneKarte:
            return True
        else:
            # da li je karta koju bacam razlicite boje od prve bacene
            if kartaKojuZelimOdigrati.boja != self.runda.bacanja[-1].baceneKarte[0].boja:
                # da li imam te boje a bacio sam neku drugu                
                bojeKojeImam = [karta.boja for karta in mojeKarte]
                # ako imam
                if self.runda.bacanja[-1].baceneKarte[0].boja in bojeKojeImam:
                    return False
                # ako nemam
                else:
                    # ako karta kou zelim baciti nije adut ...
                    if kartaKojuZelimOdigrati.boja != self.runda.adut:
                        # ako nije adut, a ja imam aduta onda
                        if self.runda.adut in bojeKojeImam:
                            return False
                    # ako je adut
                    else:
                        # da li u bacenim kartama ima vece u adutu od one koju ja zelim baciti?
                        if any(karta.jacinaKarte(self.runda.adut) > kartaKojuZelimOdigrati.jacinaKarte(self.runda.adut)
                               for karta in self.runda.bacanja[-1].baceneKarte if karta.boja == self.runda.adut):
                            # ako da, da li ja imam vece od najvece?
                            if any(karta > max(najjacakarta.jacinaKarte(self.runda.adut) for najjacakarta in
                                               self.runda.bacanja[-1].baceneKarte if
                                               najjacakarta.boja == self.runda.adut) for karta in mojeKarte if
                                   karta.boja == self.runda.adut):
                                return False

            # ako je karta iste boje
            else:
                # provjera da li zelim baciti kartu koja je slabija od one na stolu
                if any(karta.jacinaKarte(self.runda.adut) > kartaKojuZelimOdigrati.jacinaKarte(self.runda.adut) for
                       karta in self.runda.bacanja[-1].baceneKarte if
                       karta.boja == self.runda.bacanja[-1].baceneKarte[0].boja):
                    # ako da, da li ja imam vece od najvece?
                    najjacakarta = max(
                        najjacakarta.jacinaKarte(self.runda.adut) for najjacakarta in self.runda.bacanja[-1].baceneKarte
                        if najjacakarta.boja == self.runda.bacanja[-1].baceneKarte[0].boja)
                    if any(najjacakarta < karta.jacinaKarte(self.runda.adut) for karta in mojeKarte if
                           karta.boja == self.runda.bacanja[-1].baceneKarte[0].boja):
                        # ako imam vece od najvece, da li je bacam zato jer u bacenima ima aduta? .. pa ne moram baciti jacu, a ako se prvo igrao adut onda i ja moram baciti jaceg aduta
                        if not any(karta.boja == self.runda.adut for karta in self.runda.bacanja[
                            -1].baceneKarte) or kartaKojuZelimOdigrati.boja == self.runda.adut:
                            return False
            return True

    def sortirajKarte(self, karte):
        return sorted(karte, key=lambda karta: (karta.boja, karta.poredak), reverse=False)

    def provjeriZvanje(self, karte, igrac):

        sortiraneKarte = self.sortirajKarte(karte)

        prethodnaKarta = None
        nizovi = PersistentList()
        isteKarte = PersistentList()
        trenutniNiz = 1
        trenutneIste = 1

        # provjera karata u nizu iste boje
        for karta in sortiraneKarte:

            if prethodnaKarta == None:
                prethodnaKarta = karta
            else:
                if karta.poredak - prethodnaKarta.poredak == 1 and karta.boja == prethodnaKarta.boja:
                    trenutniNiz += 1
                    # da li je to zadnja karta u spilu
                    if karta == sortiraneKarte[-1]:
                        if trenutniNiz > 2:
                            nizovi.append({'broj': trenutniNiz, 'najveca': karta})
                else:
                    if trenutniNiz > 2:
                        nizovi.append({'broj': trenutniNiz, 'najveca': prethodnaKarta})
                    trenutniNiz = 1
                prethodnaKarta = karta

            for kartax in sortiraneKarte:
                if kartax.poredak == karta.poredak and kartax != karta:
                    trenutneIste += 1

            if trenutneIste == 4:
                isteKarte.append(karta)

            trenutneIste = 1

        self.redZvanja.append({'nizovi': nizovi, 'iste': isteKarte, 'igrac': igrac})

    def promijeniRedoslijed(self, n, red):
        self.redIgraca = red[n:] + red[:n]

    def nosi(self):
        # ako prva bacena karta nije adut
        if (self.runda.bacanja[-1].baceneKarte[0].boja != self.runda.adut):
            # provjeri da li u bacenima ima aduta
            if any(karta.boja == self.runda.adut for karta in self.runda.bacanja[-1].baceneKarte):
                # ako ima onda je noseca karta medu adutima
                jacinaNajjaceKarte = max(
                    karta.jacinaKarte(self.runda.adut) for karta in self.runda.bacanja[-1].baceneKarte if
                    karta.boja == self.runda.adut)
                najjacaKarta = next((karta for karta in self.runda.bacanja[-1].baceneKarte if
                                     karta.boja == self.runda.adut and karta.jacinaKarte(
                                         self.runda.adut) == jacinaNajjaceKarte), None)
            else:
                # ako nema onda je noseca karta medu obicnim kartama
                jacinaNajjaceKarte = max(
                    karta.jacinaKarte(self.runda.adut) for karta in self.runda.bacanja[-1].baceneKarte if
                    karta.boja == self.runda.bacanja[-1].baceneKarte[0].boja)
                najjacaKarta = next((karta for karta in self.runda.bacanja[-1].baceneKarte if
                                     karta.boja == self.runda.bacanja[-1].baceneKarte[0].boja and karta.jacinaKarte(
                                         self.runda.adut) == jacinaNajjaceKarte), None)

        # ako prva bacena karta je adut
        else:
            jacinaNajjaceKarte = max(
                karta.jacinaKarte(self.runda.adut) for karta in self.runda.bacanja[-1].baceneKarte if
                karta.boja == self.runda.bacanja[-1].baceneKarte[0].boja)
            najjacaKarta = next((karta for karta in self.runda.bacanja[-1].baceneKarte if
                                 karta.boja == self.runda.bacanja[-1].baceneKarte[0].boja and karta.jacinaKarte(
                                     self.runda.adut) == jacinaNajjaceKarte), None)

        # dohvati index bacene karte (index je takoder i index igraca u reduIgraca)
        print "............."
        index = self.runda.bacanja[-1].baceneKarte.index(najjacaKarta)
        if index not in [0, 1, 2, 3]:
            print "Krivo!"
        print "Bacanje nosi: " + self.redIgraca[index].nadimak
        self.promijeniRedoslijed(index, self.redIgraca)
        if self.redIgraca[index] in self.timovi[0].igraci:
            self.miRunda += sum(karta.vrijednostKarte(self.runda.adut) for karta in self.runda.bacanja[-1].baceneKarte)
        else:
            self.viRunda += sum(karta.vrijednostKarte(self.runda.adut) for karta in self.runda.bacanja[-1].baceneKarte)
        print "Runda mi: " + str(self.miRunda)
        print "Runda vi: " + str(self.viRunda)
        transaction.commit()


class Tim(Persistent):
    def __init__(self):
        self.igraci = PersistentList()

    def dodajNovogIgraca(self, igrac):
        self.igraci.append(igrac)


class Spil(Persistent):
    def __init__(self, karte, boje):
        self.karte = PersistentList()
        for key, value in boje.iteritems():
            for karta in karte:
                novaKarta = Karta(karta["oznaka"], key, karta['naziv'], karta['vrijednost'],
                                  karta['vrijednostAduta'], karta['jacina'], karta['poredak'], karta['jacinaAduta'])
                self.karte.append(novaKarta)

    def promijesaj(self):
        random.shuffle(self.karte)

    def podijeli(self):
        karteIgraca = PersistentList()
        karteIgraca.extend(self.karte[:8])
        del self.karte[:8]
        return karteIgraca


class Karta(Persistent):
    def __init__(self, oznaka, boja, naziv, vrijednost, vrijednostAduta, jacina, poredak, jacinaAduta):
        self.slika = 'img/' + oznaka + BOJE[boja][0] + '.png'
        self.boja = boja
        self.vrijednost = vrijednost
        self.naziv = naziv
        self.jacina = jacina
        self.poredak = poredak
        self.vrijednostAduta = vrijednostAduta
        self.jacinaAduta = jacinaAduta

    def __repr__(self):
        return "[" + self.boja + ", " + self.naziv + "]"

    def jeLiKartaAdut(self, adut):
        if self.boja == adut:
            return True
        else:
            return False

    def vrijednostKarte(self, adut):
        if self.jeLiKartaAdut(adut) == True:
            return self.vrijednostAduta
        else:
            return self.vrijednost

    def jacinaKarte(self, adut):
        if self.jeLiKartaAdut(adut) == True:
            return self.jacinaAduta
        else:
            return self.jacina


class Runda(Persistent):
    def __init__(self):
        self.tim1Zvanja = 0
        self.tim2Zvanja = 0
        self.bacanja = PersistentList()
        self.adut = None
        self.timKojiJeZvao = None

    def dodajBacanje(self, bacanje):
        self.bacanja.append(bacanje)

    def postaviAdut(self, boja, tim):
        self.adut = boja
        self.timKojiJeZvao = tim


class Bacanje(Persistent):
    def __init__(self):
        self.baceneKarte = PersistentList()

    def kartaBacena(self, bacenaKarta):
        self.baceneKarte.append(bacenaKarta)


class KartaSprite(pygame.sprite.DirtySprite):
    def __init__(self, karta):
        pygame.sprite.DirtySprite.__init__(self)
        self.karta = karta
        self.image = pygame.image.load(self.karta.slika)
        self.rect = self.image.get_rect()
        self.dirty = 2
        self.visible = 0

    def pozicioniraj(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def prikazi(self):
        self.visible = 1

    def sakrij(self):
        self.visible = 0


class AdutSprite(pygame.sprite.DirtySprite):
    def __init__(self, boja, slika, x, y):
        pygame.sprite.DirtySprite.__init__(self)
        self.boja = boja
        self.image = pygame.image.load(slika)
        self.rect = self.image.get_rect()
        self.dirty = 2
        self.visible = 1
        self.rect.x = x
        self.rect.y = y

    def pozicioniraj(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def prikazi(self):
        self.visible = 1

    def sakrij(self):
        self.visible = 0

class IgraSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([973, 30])
        self.image.fill((180,180,180))
        self.rect = self.image.get_rect()

        self.visible = 1
        self.rect.x = x
        self.rect.y = y

    def pozicioniraj(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def prikazi(self):
        self.visible = 1

    def sakrij(self):
        self.visible = 0

class Engine():
    def __init__(self):
        self.inicijalizirajGrafickoSucelje()
        self.spojiSeNaServer()
        self.glavnaPetlja()

    def spojiSeNaServer(self):
        #self.spremnik = ClientStorage.ClientStorage(('localhost', 1981))
        self.spremnik = ClientStorage.ClientStorage(('45.63.117.103', 1981))
        self.spremnik.server_sync = True
        self.bp = DB(self.spremnik)
        self.veza = self.bp.open()
        self.root = self.veza.root()

    def dohvatiPostojeceIgre(self):
        pass

    def igrajPostojecuIgru(self, soba):
        global karteSpritesList
        transaction.commit()
        if soba in self.root:
            igra = self.root[self.soba]
        self.igrac = Igrac(self.nadimak, False, self.root[self.soba])
        for karta in igra.spil.karte:
            kartaSprite = KartaSprite(karta)
            karteSpritesList.append(kartaSprite)
        transaction.commit()

    def kreirajNovuIgru(self):
        global karteSpritesList
        transaction.commit()
        igra = Igra(KARTE, BOJE)
        for karta in igra.spil.karte:
            kartaSprite = KartaSprite(karta)
            karteSpritesList.append(kartaSprite)
        if self.soba in self.root:
            del self.root[self.soba]
        self.root[self.soba] = igra
        transaction.commit()
        self.igrac = Igrac(self.nadimak, False, self.root[self.soba])

    def inicijalizirajGrafickoSucelje(self):
        # pygame init
        pygame.init()
        self.prozor = pygame.display.set_mode((1000, 666))
        pygame.display.set_caption("Belot - Teorija baza podataka (Karlo Grlic)")
        pygame.display.update()

        self.nadimak = "default"
        self.nadimakFont = pygame.font.SysFont("Sans", 50)
        self.nadimakLabel = self.nadimakFont.render(self.nadimak, 1, (0, 0, 0))

        self.soba = "default"
        self.sobaFont = pygame.font.SysFont("Sans", 25)
        self.sobaLabel = self.sobaFont.render(self.soba, 1, (0, 0, 0))

        self.bg = pygame.image.load("img/start.jpg")
        self.pozadinaKarte = pygame.image.load("img/back.png")
        self.exitImage = pygame.image.load("img/exit.png")

        # Pitati igraca za nick
        tkRoot = Tkinter.Tk()
        tkRoot.withdraw()

        self.prozor.blit(self.bg, (0, 0))
        self.prozor.blit(self.nadimakLabel, (362, 115))

        # Dodavanje adut spriteva u sprite group
        i = 0
        for key, value in BOJE.items():
            adutiObaveznoSprites.add(AdutSprite(key, value[1], 200 + i * 150, 250))
            adutiSprites.add(AdutSprite(key, value[1], 125 + i * 150, 250))
            i += 1
        adutiSprites.add(AdutSprite(False, 'img/no.png', 725, 250))

        pygame.display.update()

    def provjeriZastavice(self):
        global karteSpritesList
        try:
            transaction.commit()
            if self.igrac.zastavice["uzmiKarte"] == 1:
                self.igrac.zastavice["uzmiKarte"] = 0
                self.igrac.uzmiKarte()
            elif self.igrac.zastavice["hocuLiZvati"] == 1:
                # self.zastavice["hocuLiZvati"] = 0
                self.prozor.blit(
                    pygame.font.SysFont("Sans", 30).render("Na redu ste za odabir aduta!", 1, (255, 255, 255)),
                    (10, 10))
                adutiSprites.draw(self.prozor)
                if self.igrac.jeLiRacunalo == True:
                    self.igrac.hocuLiZvati(False)
            elif self.igrac.zastavice["hocuLiZvati"] == 2:
                self.prozor.blit(
                    pygame.font.SysFont("Sans", 30).render("Zadnji ste, morate zvati!", 1, (255, 255, 255)), (10, 10))
                adutiObaveznoSprites.draw(self.prozor)
                # self.igrac.zastavice["hocuLiZvati"] = 0
                if self.igrac.jeLiRacunalo == True:
                    self.igrac.hocuLiZvati(True)
            elif self.igrac.zastavice["provjeriZvanja"] == 1:
                self.igrac.zastavice["provjeriZvanja"] = 0
                self.igrac.provjeriZvanja()
            elif self.igrac.zastavice["baciKartu"] == 1:
                self.prozor.blit(
                    pygame.font.SysFont("Sans", 30).render("Na redu ste za bacanje karte!", 1, (255, 255, 255)),
                    (10, 10))
                if self.igrac.jeLiRacunalo == True:
                    self.igrac.baciKartu()
        except:
            time.sleep(.05)
        time.sleep(.01)

    def glavnaPetlja(self):

        global karteSpritesList
        global vidljiveKarteSprites
        global adutiSprites
        global adutiObaveznoSprites

        izadiIzIgre = False
        prikaz = 0
        while not izadiIzIgre:
            self.prozor.blit(self.bg, (0, 0))
            if prikaz == 0:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        izadiIzIgre = True
                    if event.type == pygame.MOUSEBUTTONUP:
                        pozicija = pygame.mouse.get_pos()
                        if pozicija[0] >= 352 and pozicija[1] >= 108 and pozicija[0] <= 852 and pozicija[1] <= 188:
                            self.nadimak = askstring("Unos nadimka", "Nadimak:")
                            self.nadimakLabel = self.nadimakFont.render(self.nadimak, 1, (0, 0, 0))
                        if pozicija[0] >= 126 and pozicija[1] >= 397 and pozicija[0] <= 350 and pozicija[1] <= 447:
                            self.bg = pygame.image.load("img/table.jpg")
                            self.kreirajNovuIgru()
                            prikaz = 1
                        if pozicija[0] >= 358 and pozicija[1] >= 356 and pozicija[0] <= 670 and pozicija[1] <= 450:
                            self.igrajPostojecuIgru(self.soba)
                            #self.bg = pygame.image.load("img/search.jpg")
                           # prikaz = 2
                            self.bg = pygame.image.load("img/table.jpg")
                            prikaz = 1
                        if pozicija[0] >= 228 and pozicija[1] >= 335 and pozicija[0] <= 350 and pozicija[1] <= 389:
                            self.soba = askstring("Naziv sobe", "Naziv:")
                            self.sobaLabel = self.sobaFont.render(self.soba, 1, (0, 0, 0))
                self.prozor.blit(self.sobaLabel, (238, 358))
                self.prozor.blit(self.nadimakLabel, (362, 115))

            if prikaz == 1:
                self.provjeriZastavice()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        izadiIzIgre = True
                    if event.type == pygame.MOUSEBUTTONUP:
                        pozicija = pygame.mouse.get_pos()
                        if pozicija[0] >= 921 and pozicija[1] >= 591 and pozicija[0] <= 1000 and pozicija[1] <= 666:
                            self.bg = pygame.image.load("img/start.jpg")
                            prikaz = 0
                        odabraneKarteSprite = [s for s in vidljiveKarteSprites if s.rect.collidepoint(pozicija)]
                        if len(odabraneKarteSprite) > 0 and self.igrac.zastavice['baciKartu'] == 1:
                            valjaniOdabir = self.igrac.baciKartu(
                                next((x for x in self.igrac.karte if x == odabraneKarteSprite[0].karta), None))
                            if (valjaniOdabir):
                                vidljiveKarteSprites.remove(odabraneKarteSprite[0])
                        if self.igrac.zastavice['hocuLiZvati'] == 1:
                            odabraniAdutSprite = [s for s in adutiSprites if s.rect.collidepoint(pozicija)]
                            if len(odabraniAdutSprite) > 0:
                                self.igrac.igra.onOdaberiAdut(odabraniAdutSprite[0].boja)
                                self.igrac.zastavice['hocuLiZvati'] = 0
                        if self.igrac.zastavice['hocuLiZvati'] == 2:
                            odabraniAdutSprite = [s for s in adutiObaveznoSprites if s.rect.collidepoint(pozicija)]
                            if len(odabraniAdutSprite) > 0:
                                self.igrac.igra.onOdaberiAdut(odabraniAdutSprite[0].boja)
                                self.igrac.zastavice['hocuLiZvati'] = 0

                # prikazi bacene karte
                if len(self.igrac.igra.runda.bacanja) > 0:
                    for i in range(len(self.igrac.igra.runda.bacanja[-1].baceneKarte)):
                        self.prozor.blit(next(
                            (x for x in karteSpritesList if x.karta == self.igrac.igra.runda.bacanja[-1].baceneKarte[i]),
                            None).image, (268 + 80 * i, 233))
                    if self.igrac in self.igrac.igra.tim1.igraci:
                        miRunda = 'Mi runda: ' + str(self.igrac.igra.miRunda)
                        miIgra = 'Mi igra: ' + str(self.igrac.igra.mi)
                        viRunda = 'Vi runda: ' + str(self.igrac.igra.viRunda)
                        viIgra = 'Vi igra: ' + str(self.igrac.igra.vi)
                    else:
                        miRunda = 'Mi runda: ' + str(self.igrac.igra.viRunda)
                        miIgra = 'Mi igra: ' + str(self.igrac.igra.vi)
                        viRunda = 'Vi runda: ' + str(self.igrac.igra.miRunda)
                        viIgra = 'Vi igra: ' + str(self.igrac.igra.mi)

                    self.prozor.blit(pygame.font.SysFont("Sans", 15).render(miRunda, 1, (255, 255, 255)),(8, 570))
                    self.prozor.blit(pygame.font.SysFont("Sans", 15).render(viRunda, 1, (255, 255, 255)), (8, 590))
                    self.prozor.blit(pygame.font.SysFont("Sans", 15).render(miIgra, 1, (255, 255, 255)), (8, 620))
                    self.prozor.blit(pygame.font.SysFont("Sans", 15).render(viIgra, 1, (255, 255, 255)), (8, 640))

                #prikazi imena igraca
                mojaPozicija = self.igrac.igra.redIgraca.index(self.igrac)
                redIgraca = self.igrac.igra.redIgraca[mojaPozicija:] + self.igrac.igra.redIgraca[:mojaPozicija]
                for i in range(len(redIgraca)):
                    if redIgraca[i].zastavice['hocuLiZvati'] == 1 or redIgraca[i].zastavice['baciKartu'] == 1:
                        font = 30
                        boja = (255, 0, 0)
                    else:
                        font = 25
                        boja = (255, 255, 255)
                    if i == 1:
                        self.prozor.blit(pygame.font.SysFont("Sans", font).render(redIgraca[i].nadimak, 1, boja), (900, 300))
                    if i == 2:
                        self.prozor.blit(pygame.font.SysFont("Sans", font).render(redIgraca[i].nadimak, 1, boja), (450, 10))
                    if i == 3:
                        self.prozor.blit(pygame.font.SysFont("Sans", font).render(redIgraca[i].nadimak, 1, boja), (10, 300))

                #prikazi igraceve karte
                vidljiveKarteSprites.draw(self.prozor)

                # prikazi odabrani adut i skrivene karte
                if self.igrac.igra.runda.adut is not None:
                    self.prozor.blit(next((x for x in adutiObaveznoSprites.sprites() if x.boja == self.igrac.igra.runda.adut), None).image, (850, 0))
                else:
                    if len(self.igrac.igra.redIgraca) == 4:
                        self.prozor.blit(self.pozadinaKarte, ((1000 - (100 * 8)) / 2 + 100 * 6, 566))
                        self.prozor.blit(self.pozadinaKarte, ((1000 - (100 * 8)) / 2 + 100 * 7, 566))

                self.prozor.blit(self.exitImage, (921, 591))


            pygame.display.update()


engine = Engine()
