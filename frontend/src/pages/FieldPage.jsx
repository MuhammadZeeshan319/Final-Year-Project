import Questionnaire from "../components/Questionnaire";
import RankingResults from "../components/RankingResults";
import { useEduPath } from "../context/eduPathContext";

// /app : questions first, then the ranked fields once the model has answered.
export default function FieldPage() {
  const { ranking } = useEduPath();
  return ranking ? <RankingResults /> : <Questionnaire />;
}
