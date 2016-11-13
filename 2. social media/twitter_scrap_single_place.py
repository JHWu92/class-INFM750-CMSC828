import datetime
import twitter_scrap
import sys

def main(pidx):
    place = [places[int(pidx)]]
    twitter_scrap.main(place, 'social_media_raw\\twitter\\nationalpark')

places = [
    ["Adams NHP", ['-71.011182','42.256466'], '2km',datetime.datetime(2099, 1, 1)],
    ["African Burial Ground NM (AFBG)", ['-74.004463','40.714527'], '2km',datetime.datetime(2099, 1, 2)],
    ["Agate Fossil Beds NM", ['-74.004463','40.714527'], '2km',datetime.datetime(2099, 1, 3)],
    ["Alibates Flint Quarries NM (ALFL)", ['-101.671703','35.581974'], '3km',datetime.datetime(2099, 1, 4)],
    ["Allegheny Portage Railroad NHS (ALPO)", ['-78.848037','40.370308'], '2km',datetime.datetime(2099, 1, 5)],
    ["Andersonville NHS (ANDE)", ['-84.129971','32.198203'], '2km',datetime.datetime(2099, 1, 6)],
    ["Aniakchak NM & PRES (ANIA)1", ['-158.11783','56.895444'], '20km',datetime.datetime(2099, 1, 7)],
    ["Aniakchak NM & PRES (ANIA)2", ['-157.900935','56.893035'], '31km',datetime.datetime(2099, 1, 8)],
    ["Antietam NB (ANTI)", ['-77.738692','39.467515'], '4km',datetime.datetime(2099, 1, 9)],
    ["Appomattox Court House NHP (APCO)", ['-78.797797','37.378384'], '3km',datetime.datetime(2099, 1, 10)],
    ["Arkansas Post NMEM (ARPO)", ['-91.345863','34.021377'], '3km',datetime.datetime(2099, 1, 11)],
    ["Arlington House The R.E. Lee MEM (ARHO)", ['-91.345863','34.021377'], '3km',datetime.datetime(2099, 1, 12)],
    ["Aztec Ruins NM (AZRU)", ['-107.999925','36.836822'], '2km',datetime.datetime(2099, 1, 13)],
    ["Bent's Old Fort NHS (BEOL)", ['-103.426621','38.039713'], '3km',datetime.datetime(2099, 1, 14)],
    ["Biscayne NP", ['-80.223698','25.497211'], '22km',datetime.datetime(2099, 1, 15)],
    ["Brown v. Board of Education NHS [larger]", ['-95.676468','39.037933'], '2km',datetime.datetime(2099, 1, 16)],
    ["Brown v. Board of Education NHS", ['-95.676483','39.03792'], '2km',datetime.datetime(2099, 1, 17)],
    ["Buck Island Reef NM", ['-64.620901','17.78715'], '2km',datetime.datetime(2099, 1, 18)],
    ["Cape Cod NS", ['-70.045823','41.935492'], '35km',datetime.datetime(2099, 1, 19)],
]

if __name__ == '__main__':
    main(sys.argv[1])