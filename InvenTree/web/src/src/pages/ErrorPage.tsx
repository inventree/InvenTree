import { Trans, t } from "@lingui/macro";
import { useDocumentTitle } from "@mantine/hooks";
import { useEffect, useState } from "react";
import { useRouteError } from "react-router-dom";
import { LanguageContext } from "../context/LanguageContext";
import { ErrorResponse } from "../context/states";
import Container from 'react-bootstrap/Container';


export default function ErrorPage() {
  const error = useRouteError() as ErrorResponse;
  const [title, setTitle] = useState(t`Error`);
  useDocumentTitle(title);

  useEffect(() => {
    if (error && error.statusText) {
      setTitle(t`Error: ${error.statusText}`);
    }
  }, [error])


  return (
    <LanguageContext>
      <Container>
        <h1><Trans>Error</Trans></h1>
        <p><Trans>Sorry, an unexpected error has occurred.</Trans></p>
        <p>
          <i>{error.statusText || error.message}</i>
        </p>
      </Container>
    </LanguageContext>
  );
}
