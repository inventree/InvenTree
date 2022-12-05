import { Trans } from "@lingui/macro";
import { useRouteError } from "react-router-dom";
import { LanguageContext } from "../context/LanguageContext";

export default function ErrorPage() {
  const error = useRouteError();

  return (
    <LanguageContext>
      <div id="error-page">
        <h1><Trans>Error</Trans></h1>
        <p><Trans>Sorry, an unexpected error has occurred.</Trans></p>
        <p>
          <i>{error.statusText || error.message}</i>
        </p>
      </div>
    </LanguageContext>
  );
}
