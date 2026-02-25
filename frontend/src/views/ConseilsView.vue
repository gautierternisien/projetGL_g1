<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import Header from '@/components/AppHeader.vue'
import { computed } from 'vue'
import { conseilHebdo } from '@/data/conseilHebdo.ts'
import { getServerWeekNumber } from '@/utils/serverTime'

const conseilActuel = computed(() => {
  const currentWeek = getServerWeekNumber()

  // L'index d'un tableau commence à 0, donc on fait -1.
  // Le modulo (%) permet de boucler : si on est semaine 53, ça revient au conseil 1.
  const index = (currentWeek - 1) % conseilHebdo.length

  return conseilHebdo[index]
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Conseils" />
    <div class="scrollable-area">
      <div>
        <!-- Conseil de la semaine -->
        <Card title="Conseil de la semaine">
          <div class="dashboard-card-content">
            <p class="dashboard-text">{{ conseilActuel }}</p>
          </div>
        </Card>

        <!-- Le saviez-vous -->
        <Card title="Le saviez-vous ?">
          <div class="dashboard-card-content">
            <p class="dashboard-text">
              Il n'y a pas que l'empreinte carbone qui importe, l'empreinte eau est aussi importante
              ! Ces deux empreintes sont complémentaires pour la gestion des ressources naturelles
              de la planète.
            </p>
          </div>
        </Card>

        <!-- Impact des services sociétaux -->
        <Card title="Impact des services sociétaux">
          <div class="dashboard-card-content">
            <p class="dashboard-text">
              Les services sociétaux correspondent à 1,4 tonnes de CO2eq, ce qui correspond à une
              grande part des objectifs de 2050 fixés à 2 tonnes ! Pour agir sur ce chiffre,
              participez à la vie politique de votre pays, votez, placez mieux votre argent,
              faites pression localement !
            </p>
          </div>
        </Card>

        <!-- Aide du gouvernement -->
        <Card title="Conseils du gouvernement">
          <div class="dashboard-card-content gov-links-container">
            <a
              href="https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/tout-savoir-sur-lindice-de-durabilite#"
              target="_blank"
              class="emoji-link"
              title="Visiter le site"
            >
              <p class="aide_text">Indice de durabilité 🔗</p>
            </a>

            <a
              href="https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/tout-savoir-sur-lindice-de-reparabilite"
              target="_blank"
              class="emoji-link"
              title="Visiter le site"
            >
              <p class="aide_text">Indice de réparabilité 🔗</p>
            </a>

            <a
              href="https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/bonus-reparation-comment-ca-marche"
              target="_blank"
              class="emoji-link"
              title="Visiter le site"
            >
              <p class="aide_text">Bonus de réparation 🔗</p>
            </a>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px 0;
  text-align: center;
}

.dashboard-text {
  font-size: 1rem;
  color: #666;
  font-weight: 500;
  max-width: 100%;
}

.aide_text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #666;
  text-decoration: underline;
}

.emoji-link {
  font-size: 2rem; /* Taille de l'emoji */
  text-decoration: none; /* Enlève le soulignement bleu moche */
  display: inline-block; /* Permet la transformation */
}

/* --- SÉPARATEURS POUR LES LIENS GOUVERNEMENT --- */

/* On force le conteneur à prendre toute la largeur et on retire le gap par défaut */
.gov-links-container {
  width: 100%;
  gap: 0 !important; /* On retire l'espace par défaut pour gérer nous-mêmes le padding */
  padding-top: 0;
  padding-bottom: 0;
}

/* Style spécifique pour ces liens */
.gov-links-container .emoji-link {
  width: 80%;
  padding: 15px 0; /* Espace vertical pour aérer */
  border-bottom: 3px solid #e0e0e0; /* La ligne de séparation grise claire */
  display: block; /* Important pour que la bordure fasse toute la largeur */
}

/* On retire la bordure du tout dernier lien pour faire propre */
.gov-links-container .emoji-link:last-child {
  border-bottom: none;
}

/* Petit ajustement pour le texte au survol */
.gov-links-container .emoji-link:hover {
  background-color: #f9f9f9; /* Optionnel : léger gris au survol */
}
</style>
