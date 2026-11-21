import sqlite3
import json

CONVERSIONS = {
    "Q-CH01-EAS-004": {
        "question_text": "Which of the following processes is a classic physiological or everyday example of an exothermic reaction?",
        "options": {
            "A": "Photosynthesis in green leaves",
            "B": "Cellular respiration (oxidation of glucose releasing energy)",
            "C": "Dissolution of ammonium chloride in water",
            "D": "Melting of ice cubes at room temperature"
        },
        "correct_option": "B",
        "explanation": "Respiration is an exothermic process because glucose combines with oxygen in the cells of our body and releases energy. Photosynthesis and melting are endothermic."
    },
    "Q-CH01-MED-002": {
        "question_text": "A student completely burns $4.00\\text{ g}$ of magnesium ribbon in an excess of oxygen inside a sealed crucible, yielding $6.67\\text{ g}$ of magnesium oxide. According to the Law of Conservation of Mass, what was the mass of oxygen consumed in this chemical combination?",
        "options": {
            "A": "1.33 g",
            "B": "2.67 g",
            "C": "4.00 g",
            "D": "10.67 g"
        },
        "correct_option": "B",
        "explanation": "By the Law of Conservation of Mass: Mass of reactants = Mass of products. Mass of Mg + Mass of O2 = Mass of MgO. Therefore, Mass of O2 = 6.67 g - 4.00 g = 2.67 g."
    },
    "Q-CH01-MED-004": {
        "question_text": "When an aqueous solution of sodium sulphate ($\\text{Na}_2\\text{SO}_4$) is mixed with barium chloride ($\\text{BaCl}_2$), what precipitate is formed and what is its color?",
        "options": {
            "A": "Barium sulphate (BaSO4), white precipitate",
            "B": "Sodium chloride (NaCl), yellow precipitate",
            "C": "Barium sulphate (BaSO4), black precipitate",
            "D": "Barium sulphide (BaS), blue precipitate"
        },
        "correct_option": "A",
        "explanation": "Na2SO4(aq) + BaCl2(aq) -> BaSO4(s) + 2NaCl(aq). A white precipitate of barium sulphate (BaSO4) is formed by double displacement precipitation."
    },
    "Q-CH01-MED-005": {
        "question_text": "In the electrolysis of acidified water (NCERT Activity 1.7), why is the volume of gas collected at the cathode twice the volume collected at the anode?",
        "options": {
            "A": "Oxygen is twice as dense as hydrogen gas",
            "B": "Water (H2O) molecules contain hydrogen and oxygen in a 2:1 stoichiometric ratio, yielding 2 volumes of H2 at cathode for every 1 volume of O2 at anode",
            "C": "Hydrogen gas dissolves more rapidly in water than oxygen",
            "D": "The electrical resistance at the anode is twice as high as at the cathode"
        },
        "correct_option": "B",
        "explanation": "Electrolysis reaction: 2H2O(l) -> 2H2(g) + O2(g). Since 2 moles of hydrogen gas are liberated at the negative cathode for every 1 mole of oxygen gas at the positive anode, the volume ratio is 2:1."
    },
    "Q-CH01-HAR-002": {
        "question_text": "A mason preparing whitewash adds solid white lumps of quicklime (compound 'X') into water. Vigorous hissing occurs and the container becomes very hot, forming compound 'Y'. When 'Y' is applied to walls, it reacts with atmospheric CO2 over 2-3 days to form a shiny thin layer of 'Z'. What are compounds X, Y, and Z?",
        "options": {
            "A": "X = Calcium oxide (CaO), Y = Calcium hydroxide [Ca(OH)2], Z = Calcium carbonate (CaCO3)",
            "B": "X = Calcium carbonate (CaCO3), Y = Calcium oxide (CaO), Z = Calcium hydroxide [Ca(OH)2]",
            "C": "X = Calcium hydroxide [Ca(OH)2], Y = Calcium oxide (CaO), Z = Calcium sulphate (CaSO4)",
            "D": "X = Calcium chloride (CaCl2), Y = Calcium hydroxide [Ca(OH)2], Z = Calcium carbonate (CaCO3)"
        },
        "correct_option": "A",
        "explanation": "CaO(s) + H2O(l) -> Ca(OH)2(aq) + heat (vigorous combination). Ca(OH)2(aq) + CO2(g) -> CaCO3(s) + H2O(l), giving a shiny finish to the walls."
    },
    "Q-CH01-HAR-003": {
        "question_text": "Decomposition reactions require energy input to split reactant bonds. Which of the following correctly pairs the form of energy with its corresponding chemical decomposition reaction?",
        "options": {
            "A": "Thermal decomposition : 2H2O -> 2H2 + O2",
            "B": "Photolytic decomposition : 2AgCl(s) --(sunlight)--> 2Ag(s) + Cl2(g)",
            "C": "Electrolytic decomposition : CaCO3 -> CaO + CO2",
            "D": "Photolytic decomposition : 2FeSO4 -> Fe2O3 + SO2 + SO3"
        },
        "correct_option": "B",
        "explanation": "Silver chloride decomposes in sunlight to produce silver and chlorine gas, representing photolytic decomposition. Decomposition of CaCO3 and FeSO4 are thermal, and water electrolysis is electrolytic."
    },
    "Q-CH01-HAR-004": {
        "question_text": "When silver articles and copper vessels are exposed to moist air over long periods, what are the specific colored chemical coatings formed on their surfaces due to corrosion?",
        "options": {
            "A": "Silver: green coating of Ag2O; Copper: black coating of CuS",
            "B": "Silver: black coating of silver sulphide (Ag2S); Copper: green coating of basic copper carbonate [CuCO3.Cu(OH)2]",
            "C": "Silver: white coating of AgCl; Copper: reddish coating of Cu2O",
            "D": "Silver: brown coating of AgNO3; Copper: blue coating of CuSO4"
        },
        "correct_option": "B",
        "explanation": "Silver reacts with sulphur in the air to form black silver sulphide (Ag2S). Copper reacts with moist carbon dioxide in the air to form a green coating of basic copper carbonate [CuCO3.Cu(OH)2]."
    },
    "Q-CH01-HAR-005": {
        "question_text": "Consider the balancing of the roasting equation: $a\\,\\text{FeS}_2 + b\\,\\text{O}_2 \\rightarrow c\\,\\text{Fe}_2\\text{O}_3 + d\\,\\text{SO}_2$. When balanced with smallest whole-number coefficients, what is the sum of the stoichiometric coefficients $(a + b + c + d)$?",
        "options": {
            "A": "19",
            "B": "21",
            "C": "25",
            "D": "27"
        },
        "correct_option": "C",
        "explanation": "Balanced equation: 4 FeS2 + 11 O2 -> 2 Fe2O3 + 8 SO2. The coefficients are a=4, b=11, c=2, d=8. Sum = 4 + 11 + 2 + 8 = 25."
    },
    "Q-CH02-SA-001": {
        "question_text": "Why does rainwater conduct electricity whereas distilled water does not?",
        "options": {
            "A": "Distilled water contains dissolved gases that block electric charge",
            "B": "Rainwater dissolves atmospheric gases like CO2 and SO2 to form acids that dissociate into mobile ions, whereas distilled water contains no dissolved ions",
            "C": "Rainwater has a much higher temperature than distilled water",
            "D": "Distilled water molecules are non-polar while rainwater is ionic"
        },
        "correct_option": "B",
        "explanation": "Rainwater dissolves atmospheric CO2 forming carbonic acid (H2CO3) which dissociates into H+ and HCO3- ions, conducting electricity. Distilled water is pure and devoid of free mobile ions."
    },
    "Q-CH05-SA-001": {
        "question_text": "Which of the following correctly distinguishes an artery from a vein regarding wall structure and blood pressure?",
        "options": {
            "A": "Arteries have thin walls and valves, carrying blood at low pressure",
            "B": "Arteries have thick, elastic walls to withstand high pumping pressure from the heart; veins have thin walls with valves to prevent backflow",
            "C": "Veins have thick muscular walls to push blood to lungs under high pressure",
            "D": "Both have identical wall thickness but veins possess no internal valves"
        },
        "correct_option": "B",
        "explanation": "Arteries carry blood away from the heart at high, pulsating pressure, requiring thick elastic walls. Veins collect blood at low pressure and have valves to ensure unidirectional flow back to the heart."
    },
    "Q-CH07-SA-001": {
        "question_text": "Which of the following is a primary horticultural advantage of vegetative propagation over seed propagation?",
        "options": {
            "A": "It produces immense genetic variability in every progeny generation",
            "B": "Plants raised through vegetative propagation bear flowers and fruits earlier and retain exact parental genetic qualities",
            "C": "It eliminates the need for photosynthesis and moisture",
            "D": "Vegetative plants produce significantly more seeds per fruit"
        },
        "correct_option": "B",
        "explanation": "Vegetative propagation allows plants to bear flowers and fruits earlier than seed-grown plants. It also enables the propagation of seedless plants (banana, orange, rose, jasmine) and ensures genetic uniformity."
    },
    "Q-CH09-NUM-001": {
        "question_text": "A concave mirror produces a three times magnified real image of an object placed at $10\\text{ cm}$ in front of it. What is the focal length of the mirror?",
        "options": {
            "A": "-15 cm",
            "B": "-7.5 cm",
            "C": "+7.5 cm",
            "D": "-30 cm"
        },
        "correct_option": "B",
        "explanation": "Real image: magnification m = -3 = -v/u. With u = -10 cm, v = -30 cm. Mirror formula: 1/f = 1/v + 1/u = 1/(-30) + 1/(-10) = (-1 - 3)/30 = -4/30 = -2/15. Therefore f = -15/2 = -7.5 cm."
    },
    "Q-CH11-SA-001": {
        "question_text": "Why are the heating elements of electric toasters and electric irons made of alloys (such as Nichrome) rather than pure metals?",
        "options": {
            "A": "Alloys have lower electrical resistivity and oxidize easily",
            "B": "Alloys have higher resistivity than pure metals and do not oxidize (burn) readily at high temperatures",
            "C": "Alloys conduct heat slower and melt easily to break circuits",
            "D": "Pure metals cannot conduct alternating current"
        },
        "correct_option": "B",
        "explanation": "The resistivity of an alloy is generally higher than that of its constituent metals, and alloys do not oxidize (burn) readily at high temperatures (red-hot condition). Thus, they are ideal for heating appliances."
    },
    "Q-CH12-SA-001": {
        "question_text": "According to Fleming's Left-Hand Rule, what do the Forefinger, Middle finger, and Thumb represent when held mutually perpendicular?",
        "options": {
            "A": "Forefinger: Motion, Middle: Magnetic Field, Thumb: Current",
            "B": "Forefinger: Magnetic Field, Middle: Electric Current, Thumb: Force / Direction of Motion",
            "C": "Forefinger: Current, Middle: Force, Thumb: Magnetic Field",
            "D": "Forefinger: Induced Current, Middle: Motion, Thumb: Magnetic Field"
        },
        "correct_option": "B",
        "explanation": "Fleming's Left-Hand Rule: Forefinger points in direction of Magnetic field, Middle finger in direction of Current, and Thumb points in direction of Force (Motion) exerted on the conductor."
    },
    "Q-CH01-SA-002": {
        "question_text": "In the redox reaction $2\\text{H}_2\\text{S} + \\text{SO}_2 \\rightarrow 3\\text{S} + 2\\text{H}_2\\text{O}$, identify the oxidizing agent and the reducing agent:",
        "options": {
            "A": "Oxidizing agent: H2S; Reducing agent: SO2",
            "B": "Oxidizing agent: SO2; Reducing agent: H2S",
            "C": "Oxidizing agent: S; Reducing agent: H2O",
            "D": "Oxidizing agent: H2O; Reducing agent: SO2"
        },
        "correct_option": "B",
        "explanation": "SO2 provides oxygen / removes hydrogen (is reduced to S), so SO2 is the oxidizing agent. H2S loses hydrogen (is oxidized to S), so H2S is the reducing agent."
    },
    "Q-CH02-SA-002": {
        "question_text": "A dry pellet of a common base 'X', when exposed to open air, absorbs moisture and turns sticky. It is manufactured industrially by the chlor-alkali process. What is compound 'X'?",
        "options": {
            "A": "Calcium hydroxide [Ca(OH)2]",
            "B": "Sodium hydroxide [NaOH]",
            "C": "Sodium hydrogen carbonate [NaHCO3]",
            "D": "Potassium sulphate [K2SO4]"
        },
        "correct_option": "B",
        "explanation": "Compound X is sodium hydroxide (NaOH). Pellets of NaOH are deliquescent and absorb moisture and CO2 from the atmosphere. It is manufactured by the electrolysis of brine (chlor-alkali process)."
    },
    "Q-CH03-SA-002": {
        "question_text": "During the formation of ionic magnesium chloride ($\\text{MgCl}_2$), how do electron transfers occur between magnesium and chlorine atoms?",
        "options": {
            "A": "Magnesium atom shares two pairs of electrons equally with one chlorine atom",
            "B": "Magnesium atom (2,8,2) loses two valence electrons to form Mg2+, transferring one electron to each of two chlorine atoms (2,8,7) to form two Cl- ions",
            "C": "Two magnesium atoms transfer one electron each to one chlorine atom",
            "D": "Chlorine atom transfers seven valence electrons to magnesium to complete its octet"
        },
        "correct_option": "B",
        "explanation": "Mg (2,8,2) loses 2 electrons -> Mg2+ + 2e-. Each Cl (2,8,7) gains 1 electron -> Cl-. Electrostatic attraction holds Mg2+ and two Cl- ions together as MgCl2."
    },
    "Q-CH05-SA-002": {
        "question_text": "In the human nephron, where does the initial ultrafiltration of blood under high hydrostatic pressure take place?",
        "options": {
            "A": "Loop of Henle",
            "B": "Collecting duct",
            "C": "Glomerulus inside Bowman's capsule",
            "D": "Urinary bladder exit"
        },
        "correct_option": "C",
        "explanation": "Blood enters the kidney through the renal artery, branching into a tuft of capillaries called the glomerulus nestled in Bowman's capsule, where initial filtration under high pressure takes place."
    },
    "Q-CH08-SA-002": {
        "question_text": "How is the biological sex of a human newborn child genetically determined during fertilization?",
        "options": {
            "A": "Purely by the nutritional state and age of the mother",
            "B": "By the type of sperm cell (carrying either an X or Y chromosome) that fertilizes the ovum (which always contributes an X chromosome)",
            "C": "By environmental incubation temperature during embryonic development",
            "D": "By mitochondrial DNA inherited strictly from the father"
        },
        "correct_option": "B",
        "explanation": "All human eggs carry an X chromosome (22+X). Sperm cells can carry either an X chromosome (yielding female 44+XX) or a Y chromosome (yielding male 44+XY). Thus, the father's gamete determines the sex."
    },
    "Q-CH10-SA-002": {
        "question_text": "A student cannot see distant objects distinctly beyond $1.2\\text{ m}$. What is the vision defect and which type of corrective lens will restore normal vision?",
        "options": {
            "A": "Hypermetropia; Convex lens of suitable focal length",
            "B": "Myopia (near-sightedness); Concave lens of suitable power",
            "C": "Presbyopia; Bifocal lens with convex upper segment",
            "D": "Cataract; Surgical intraocular lens replacement only"
        },
        "correct_option": "B",
        "explanation": "Inability to see distant objects clearly indicates myopia (near-sightedness). A concave (diverging) lens of appropriate focal length diverges rays so they focus precisely on the retina."
    },
    "Q-CH11-NUM-002": {
        "question_text": "An electric lamp of resistance $20\\,\\Omega$ and a conductor of $4\\,\\Omega$ are connected in series to a $6\\text{ V}$ battery. What is the electric current flowing through the circuit?",
        "options": {
            "A": "1.50 A",
            "B": "0.25 A",
            "C": "0.30 A",
            "D": "24.0 A"
        },
        "correct_option": "B",
        "explanation": "Total resistance in series Rs = R1 + R2 = 20 ohm + 4 ohm = 24 ohm. By Ohm's law, I = V / Rs = 6 V / 24 ohm = 0.25 A."
    },
    "Q-CH04-LA-001": {
        "question_text": "Which of the following is a fundamental characteristic of a homologous series of carbon compounds?",
        "options": {
            "A": "All members have identical boiling points regardless of molar mass",
            "B": "Successive members differ by a -CH2- unit (14 u in molecular mass) and share the same functional group and similar chemical properties",
            "C": "Each member possesses a completely different general chemical formula",
            "D": "Members are structural isomers that share the exact same molecular formula"
        },
        "correct_option": "B",
        "explanation": "A homologous series is a group of organic compounds having the same functional group, where adjacent members differ by a -CH2- group (14 u). They exhibit similar chemical properties and a gradual gradation in physical properties."
    },
    "Q-CH05-LA-001": {
        "question_text": "In human double circulation, which chamber of the heart pumps oxygenated blood under highest pressure into the systemic aorta to supply the entire body?",
        "options": {
            "A": "Right atrium",
            "B": "Right ventricle",
            "C": "Left ventricle",
            "D": "Left atrium"
        },
        "correct_option": "C",
        "explanation": "The left ventricle has thick muscular walls because it must pump oxygenated blood under high pressure through the aorta to all organs throughout the entire body."
    },
    "Q-CH11-LA-001": {
        "question_text": "When three resistors $R_1$, $R_2$, and $R_3$ are connected in series across a voltage source $V$, what is the correct relationship for equivalent resistance $R_s$ and current $I$?",
        "options": {
            "A": "Rs = R1 + R2 + R3, and the identical electric current I flows through every resistor",
            "B": "1/Rs = 1/R1 + 1/R2 + 1/R3, and voltage V is identical across each resistor",
            "C": "Rs = (R1 * R2 * R3) / (R1 + R2 + R3), and current splits into three unequal branches",
            "D": "Rs = R1 + R2 - R3, and current decreases along the circuit"
        },
        "correct_option": "A",
        "explanation": "In a series circuit, current I is uniform throughout. The total voltage V = V1 + V2 + V3 = I*R1 + I*R2 + I*R3 = I*(R1 + R2 + R3). Therefore Rs = R1 + R2 + R3."
    },
    "Q-CH02-CB-001": {
        "question_text": "During hyperacidity in the human stomach, excess hydrochloric acid causes pain and irritation. Which mild basic substance is commonly used in antacids to safely neutralize this acid without irritating gastric mucosa?",
        "options": {
            "A": "Concentrated potassium hydroxide [KOH]",
            "B": "Magnesium hydroxide [Milk of Magnesia, Mg(OH)2] or Sodium hydrogen carbonate [NaHCO3]",
            "C": "Calcium oxychloride (Bleaching powder) [CaOCl2]",
            "D": "Copper sulphate pentahydrate [CuSO4.5H2O]"
        },
        "correct_option": "B",
        "explanation": "Antacids are mild bases such as magnesium hydroxide [Mg(OH)2, Milk of Magnesia] and sodium hydrogen carbonate (baking soda) that neutralize excess hydrochloric acid in the stomach to relieve indigestion."
    },
    "Q-CH09-CB-001": {
        "question_text": "A student places a candle flame at $30\\text{ cm}$ in front of a convex lens of focal length $f = 15\\text{ cm}$. What are the position, nature, and magnification of the image formed on the screen?",
        "options": {
            "A": "At 15 cm on the same side; virtual, erect, m = +1.0",
            "B": "At 30 cm on the other side of lens (at 2F2); real, inverted, same size (m = -1.0)",
            "C": "At infinity; real, inverted, highly enlarged (m = -infinity)",
            "D": "Between F and 2F; virtual, inverted, m = -0.5"
        },
        "correct_option": "B",
        "explanation": "Here u = -30 cm and f = +15 cm. Since u = 2f (object is at 2F1), the convex lens forms a real, inverted image at 2F2 (v = +30 cm) on the opposite side, with magnification m = v/u = +30/(-30) = -1.0."
    },
    "Q-CH08-CB-001": {
        "question_text": "In Mendel's monohybrid cross of pure round seeds (RR) with wrinkled seeds (rr), what phenotypic ratio and count of round vs wrinkled seeds are obtained in an $F_2$ generation of 1,600 pea plants?",
        "options": {
            "A": "1:1 ratio; 800 Round and 800 Wrinkled seeds",
            "B": "3:1 ratio; 1,200 Round and 400 Wrinkled seeds",
            "C": "9:3:3:1 ratio; 900 Round, 300 Wrinkled, 400 Mixed seeds",
            "D": "2:1 ratio; 1,066 Round and 534 Wrinkled seeds"
        },
        "correct_option": "B",
        "explanation": "The F2 phenotypic ratio for a monohybrid cross is 3:1 (dominant : recessive). Out of 1,600 seeds: Round seeds = (3/4)*1600 = 1,200; Wrinkled seeds = (1/4)*1600 = 400."
    }
}

def migrate_to_mcq():
    conn = sqlite3.connect('data/curriculum.db')
    c = conn.cursor()

    count = 0
    for qid, data in CONVERSIONS.items():
        ak_dict = {
            "options": data["options"],
            "correct_option": data["correct_option"]
        }
        ak_json = json.dumps(ak_dict)

        c.execute('''
        UPDATE questions
        SET question_type = 'MCQ',
            question_text = ?,
            answer_key_json = ?,
            explanation = ?
        WHERE question_id = ?
        ''', (data["question_text"], ak_json, data["explanation"], qid))
        count += c.rowcount

    conn.commit()
    print(f"Successfully converted {count} questions to MCQ.")

    c.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type;")
    print("New question distribution:", c.fetchall())

    conn.close()

if __name__ == '__main__':
    migrate_to_mcq()
