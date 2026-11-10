export function InjectionBadge() {
  return (
    <div className="injection" role="alert">
      <strong>Wykryto podejrzaną treść.</strong> Dokument zawiera fragmenty wyglądające na polecenia
      dla systemu AI. Zostały zignorowane, ale potraktuj wyniki ostrożnie.
    </div>
  );
}
