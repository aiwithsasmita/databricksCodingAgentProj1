import { Hospital, OrgType, Specialty, BillingPattern } from "./types";

const orgTypes: OrgType[] = ["Hospital", "Nursing Home", "Clinic", "Rehab Center"];
const specialties: Specialty[] = ["Cardiology", "Orthopedics", "General", "Oncology", "Neurology", "Pediatrics", "Pulmonology", "Gastroenterology"];
const billingPatterns: BillingPattern[] = ["High Volume", "Moderate", "Low Volume", "Outlier"];

const locations: { name: string; city: string; state: string; zip: string; lat: number; lng: number }[] = [
  { name: "Metro General Hospital", city: "New York", state: "NY", zip: "10001", lat: 40.7128, lng: -74.006 },
  { name: "Cedars Health Center", city: "Los Angeles", state: "CA", zip: "90048", lat: 34.0749, lng: -118.3805 },
  { name: "Lakeside Medical", city: "Chicago", state: "IL", zip: "60614", lat: 41.9216, lng: -87.6538 },
  { name: "Gulf Coast Hospital", city: "Houston", state: "TX", zip: "77030", lat: 29.7069, lng: -95.3985 },
  { name: "Valley Care Clinic", city: "Phoenix", state: "AZ", zip: "85004", lat: 33.4484, lng: -112.074 },
  { name: "Liberty Medical Center", city: "Philadelphia", state: "PA", zip: "19104", lat: 39.9526, lng: -75.1652 },
  { name: "Alamo Health System", city: "San Antonio", state: "TX", zip: "78229", lat: 29.5095, lng: -98.5694 },
  { name: "Bayview Regional", city: "San Diego", state: "CA", zip: "92103", lat: 32.7457, lng: -117.1611 },
  { name: "Lone Star Nursing Home", city: "Dallas", state: "TX", zip: "75201", lat: 32.789, lng: -96.7985 },
  { name: "Peachtree Rehab", city: "Atlanta", state: "GA", zip: "30308", lat: 33.7713, lng: -84.3656 },
  { name: "Sunshine Clinic", city: "Miami", state: "FL", zip: "33136", lat: 25.7891, lng: -80.2102 },
  { name: "Emerald City Hospital", city: "Seattle", state: "WA", zip: "98104", lat: 47.6062, lng: -122.3321 },
  { name: "Rocky Mountain Medical", city: "Denver", state: "CO", zip: "80204", lat: 39.7392, lng: -104.9903 },
  { name: "Capital Health", city: "Washington", state: "DC", zip: "20001", lat: 38.9072, lng: -77.0369 },
  { name: "Pilgrim Nursing Home", city: "Boston", state: "MA", zip: "02114", lat: 42.3601, lng: -71.0589 },
  { name: "Desert Springs Hospital", city: "Las Vegas", state: "NV", zip: "89109", lat: 36.1699, lng: -115.1398 },
  { name: "Great Lakes Clinic", city: "Detroit", state: "MI", zip: "48201", lat: 42.3442, lng: -83.0568 },
  { name: "Magnolia Medical", city: "Nashville", state: "TN", zip: "37203", lat: 36.1627, lng: -86.7816 },
  { name: "Harbor View Rehab", city: "Baltimore", state: "MD", zip: "21201", lat: 39.2904, lng: -76.6122 },
  { name: "Heartland Hospital", city: "Kansas City", state: "MO", zip: "64108", lat: 39.0997, lng: -94.5786 },
  { name: "Palmetto Health", city: "Charlotte", state: "NC", zip: "28202", lat: 35.2271, lng: -80.8431 },
  { name: "Gateway Medical", city: "St. Louis", state: "MO", zip: "63103", lat: 38.6270, lng: -90.1994 },
  { name: "Prairie View Nursing", city: "Minneapolis", state: "MN", zip: "55415", lat: 44.9778, lng: -93.2650 },
  { name: "Cascade Clinic", city: "Portland", state: "OR", zip: "97204", lat: 45.5152, lng: -122.6784 },
  { name: "Iron City Rehab", city: "Pittsburgh", state: "PA", zip: "15213", lat: 40.4443, lng: -79.9533 },
  { name: "Arch Health Hospital", city: "Cincinnati", state: "OH", zip: "45202", lat: 39.1031, lng: -84.5120 },
  { name: "Silver Lake Medical", city: "Milwaukee", state: "WI", zip: "53202", lat: 43.0389, lng: -87.9065 },
  { name: "Bayou Medical Center", city: "New Orleans", state: "LA", zip: "70112", lat: 29.9511, lng: -90.0715 },
  { name: "Sunbelt Nursing Home", city: "Tampa", state: "FL", zip: "33602", lat: 27.9506, lng: -82.4572 },
  { name: "Pioneer Hospital", city: "Salt Lake City", state: "UT", zip: "84101", lat: 40.7608, lng: -111.891 },
  { name: "Blue Ridge Clinic", city: "Raleigh", state: "NC", zip: "27601", lat: 35.7796, lng: -78.6382 },
  { name: "Crossroads Medical", city: "Indianapolis", state: "IN", zip: "46204", lat: 39.7684, lng: -86.1581 },
  { name: "Heritage Health", city: "Columbus", state: "OH", zip: "43215", lat: 39.9612, lng: -82.9988 },
  { name: "Coastal Rehab Center", city: "Jacksonville", state: "FL", zip: "32202", lat: 30.3322, lng: -81.6557 },
  { name: "Summit Hospital", city: "San Jose", state: "CA", zip: "95113", lat: 37.3382, lng: -121.8863 },
  { name: "Capital Nursing Home", city: "Austin", state: "TX", zip: "78701", lat: 30.2672, lng: -97.7431 },
  { name: "Frontier Medical", city: "Oklahoma City", state: "OK", zip: "73102", lat: 35.4676, lng: -97.5164 },
  { name: "Brookside Clinic", city: "Louisville", state: "KY", zip: "40202", lat: 38.2527, lng: -85.7585 },
  { name: "Northern Lights Hospital", city: "Anchorage", state: "AK", zip: "99501", lat: 61.2181, lng: -149.9003 },
  { name: "Aloha Medical Center", city: "Honolulu", state: "HI", zip: "96813", lat: 21.3069, lng: -157.8583 },
  { name: "Evergreen Nursing Home", city: "Boise", state: "ID", zip: "83702", lat: 43.615, lng: -116.2023 },
  { name: "Cornfield Health", city: "Des Moines", state: "IA", zip: "50309", lat: 41.5868, lng: -93.625 },
  { name: "Sunflower Hospital", city: "Wichita", state: "KS", zip: "67202", lat: 37.6872, lng: -97.3301 },
  { name: "Bluegrass Rehab", city: "Lexington", state: "KY", zip: "40507", lat: 38.0406, lng: -84.5037 },
  { name: "Pine State Clinic", city: "Portland", state: "ME", zip: "04101", lat: 43.6591, lng: -70.2568 },
  { name: "Old Line Medical", city: "Annapolis", state: "MD", zip: "21401", lat: 38.9784, lng: -76.4922 },
  { name: "Motor City Nursing", city: "Grand Rapids", state: "MI", zip: "49503", lat: 42.9634, lng: -85.6681 },
  { name: "North Star Hospital", city: "Duluth", state: "MN", zip: "55802", lat: 46.7867, lng: -92.1005 },
  { name: "Ozark Medical", city: "Springfield", state: "MO", zip: "65806", lat: 37.2090, lng: -93.2923 },
  { name: "Big Sky Clinic", city: "Billings", state: "MT", zip: "59101", lat: 45.7833, lng: -108.5007 },
  { name: "Cornhusker Health", city: "Omaha", state: "NE", zip: "68102", lat: 41.2565, lng: -95.9345 },
  { name: "Granite State Rehab", city: "Manchester", state: "NH", zip: "03101", lat: 42.9956, lng: -71.4548 },
  { name: "Garden State Hospital", city: "Newark", state: "NJ", zip: "07102", lat: 40.7357, lng: -74.1724 },
  { name: "Enchantment Nursing", city: "Albuquerque", state: "NM", zip: "87102", lat: 35.0844, lng: -106.6504 },
  { name: "Empire Medical", city: "Buffalo", state: "NY", zip: "14202", lat: 42.8864, lng: -78.8784 },
  { name: "Buckeye Clinic", city: "Cleveland", state: "OH", zip: "44113", lat: 41.4993, lng: -81.6944 },
  { name: "Sooner Hospital", city: "Tulsa", state: "OK", zip: "74103", lat: 36.1540, lng: -95.9928 },
  { name: "Beaver State Rehab", city: "Eugene", state: "OR", zip: "97401", lat: 44.0521, lng: -123.0868 },
  { name: "Keystone Medical", city: "Harrisburg", state: "PA", zip: "17101", lat: 40.2732, lng: -76.8867 },
  { name: "Ocean State Clinic", city: "Providence", state: "RI", zip: "02903", lat: 41.824, lng: -71.4128 },
  { name: "Palmetto Nursing Home", city: "Charleston", state: "SC", zip: "29401", lat: 32.7765, lng: -79.9311 },
  { name: "Rushmore Hospital", city: "Sioux Falls", state: "SD", zip: "57104", lat: 43.5460, lng: -96.7313 },
  { name: "Volunteer Medical", city: "Memphis", state: "TN", zip: "38103", lat: 35.1495, lng: -90.049 },
  { name: "Sagebrush Clinic", city: "Cheyenne", state: "WY", zip: "82001", lat: 41.1400, lng: -104.8202 },
  { name: "Green Mountain Rehab", city: "Burlington", state: "VT", zip: "05401", lat: 44.4759, lng: -73.2121 },
  { name: "Old Dominion Hospital", city: "Richmond", state: "VA", zip: "23219", lat: 37.5407, lng: -77.436 },
  { name: "Badger Health", city: "Madison", state: "WI", zip: "53703", lat: 43.0731, lng: -89.4012 },
  { name: "Mountain State Nursing", city: "Charleston", state: "WV", zip: "25301", lat: 38.3498, lng: -81.6326 },
  { name: "Peach State Medical", city: "Savannah", state: "GA", zip: "31401", lat: 32.0809, lng: -81.0912 },
  { name: "Constitution Clinic", city: "Hartford", state: "CT", zip: "06103", lat: 41.7658, lng: -72.6734 },
  { name: "Diamond State Hospital", city: "Wilmington", state: "DE", zip: "19801", lat: 39.7391, lng: -75.5398 },
  { name: "Hoosier Rehab Center", city: "Fort Wayne", state: "IN", zip: "46802", lat: 41.0793, lng: -85.1394 },
  { name: "Pelican Medical", city: "Baton Rouge", state: "LA", zip: "70801", lat: 30.4515, lng: -91.1871 },
  { name: "Bay State Hospital", city: "Worcester", state: "MA", zip: "01608", lat: 42.2626, lng: -71.8023 },
  { name: "Tar Heel Nursing Home", city: "Greensboro", state: "NC", zip: "27401", lat: 36.0726, lng: -79.792 },
  { name: "Treasure Valley Clinic", city: "Nampa", state: "ID", zip: "83651", lat: 43.5407, lng: -116.5635 },
  { name: "Show Me Hospital", city: "Columbia", state: "MO", zip: "65201", lat: 38.9517, lng: -92.3341 },
  { name: "Centennial Medical", city: "Colorado Springs", state: "CO", zip: "80903", lat: 38.8339, lng: -104.8214 },
  { name: "Crescent City Rehab", city: "Shreveport", state: "LA", zip: "71101", lat: 32.5252, lng: -93.7502 },
  { name: "Prairie Wind Nursing", city: "Fargo", state: "ND", zip: "58102", lat: 46.8772, lng: -96.7898 },
];

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

const rand = seededRandom(42);
const pick = <T>(arr: T[]): T => arr[Math.floor(rand() * arr.length)];
const randBetween = (min: number, max: number) => Math.floor(rand() * (max - min + 1)) + min;

export const hospitals: Hospital[] = locations.map((loc, i) => {
  const orgType = orgTypes[i % orgTypes.length];
  const bedCount = orgType === "Hospital" ? randBetween(150, 800) :
                   orgType === "Nursing Home" ? randBetween(50, 250) :
                   orgType === "Clinic" ? randBetween(10, 60) :
                   randBetween(30, 120);

  const hasMismatch = rand() > 0.6;
  const billingLoc = hasMismatch ? locations[Math.floor(rand() * locations.length)] : loc;

  return {
    npi: String(1000000000 + i * 111111),
    name: loc.name,
    orgType,
    specialty: pick(specialties),
    latitude: loc.lat,
    longitude: loc.lng,
    serviceAddress: {
      street: `${randBetween(100, 9999)} ${loc.city} Blvd`,
      city: loc.city,
      state: loc.state,
      zip: loc.zip,
    },
    billingAddress: {
      street: `${randBetween(100, 9999)} Commerce Dr`,
      city: billingLoc.city,
      state: billingLoc.state,
      zip: billingLoc.zip,
    },
    billingLat: billingLoc.lat,
    billingLng: billingLoc.lng,
    bedCount,
    totalPayment: randBetween(500000, 25000000),
    billingPattern: pick(billingPatterns),
    billingEfficiency: Math.round(rand() * 40 + 60) / 100,
    claimCount: randBetween(200, 8000),
  };
});
