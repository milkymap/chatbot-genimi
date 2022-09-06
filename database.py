quiz = {
    "niveau1":{
        'threshold': 16,
        'target': "il vous faut au moins 16point sur 20", 
        'content': {
            0: {
                'target': "12 points",
                'type': 'word',
                'content': {
                    'consigne': 'lis les mots suivants', 
                    'value': [
                        'Magnifique', 'Spectateur', 'Déségréable', 'Perfection', 'Inspectrice', 'Boulangerie', 
                        'Instrument', 'Bibliothèque', 'Préparation', 'Phacochère', 'Douloureux', 'Naturellement'
                    ]
                }
            }, 
            1: {
                'target': "8 points",
                'type': 'word',
                'content': {
                    'consigne': 'lis les mots suivants', 
                    'value': [
                    'vache', 'photo', 'brodé', 'plâtre', 
                        'policier', 'pharmacien', 'gendarme', 'chauffeur'
                    ]
                }
            }
        }
    },

    "niveau2":{
        'threshold': 1,  # 1mn 5
        'target': "fluidité", 
        'content': {
            0: {
                'target': "pas plus de 1mn 5secondes", 
                'type': 'text',
                'content': {
                    'duration': 65,
                    'consigne': 'List le texte suivant à haute voix', 
                    'value': "De nos jours, la lecture devient de moins en moins pratiquée, chez les jeunes comme chez les adultes, malgré ses nombreux avantages.\nD'abord, la lecture développe l'imagination et la créativité. La lecture est une ouverture sur un monde enchanté qui nous fait rejoindre les auteur. On s'identifie au héros, on épouse ses aventures, ses sentiments ; on sort ainsi de nous-mêmes et on vit plusieurs vies.\nEnsuite, le fait de lire aide à enrichir son vocabulaire et à renforcer son emprise sur la langue.\nChaque fois que nous lisons un nouveau roman ou une fiction, nous rencontrons plusieurs mots nouveaux."
                }
            }
        }
    },

    "niveau3":{
        'threshold': 1, # 2mn
        'target': "fluidité", 
        'content': {
            0: {
                'target': "pas plus de 2mn", 
                'type': 'text',
                'content': {
                    'duration': 120, 
                    'consigne': 'List le texte suivant à haute voix', 
                    'value': "Lorsque nous sommes entièrement honnêtes, nous avons la paix de l'esprit et nous gardons notre respect de nous-mêmes. Nous acquérons une plus grande force de caractère; et nous sommes dignes de confiance aux yeux des personnes de notre entourage. En revanche, si nous sommes malhonnêtes en paroles ou en actions, nous nous faisons du mal et souvent aussi aux autres. Si nous mentons, volons, trichons, ou négligeons de fournir un travail complet pour notre salaire, nous perdons le respect de nous-mêmes et celui des membres de notre famille et de nos amis. Être honnête demande souvent du courage et des sacrifices, surtout quand les gens essaient de nous persuader de justifier un comportement malhonnête. Si nous nous trouvons dans une telle situation, souvenons-nous que la paix durable qu'apporte l'honnêteté vaut plus que le soulagement momentané qui découle du fait de faire comme tout le monde."
                }
            }
        }
    }
}
