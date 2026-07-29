import { Outlet } from "react-router-dom";

import { Button } from "@swo/design-system/button";
import { Card } from "@swo/design-system/card";
import { Navigation } from "@swo/design-system/navigation";
import { BoldText, RegularText } from "@swo/design-system/text";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { NEWS_SECTIONS, PATHS } from "~features/sandboxStanalone/paths";
import { CreateUserStandaloneModal } from "~features/sandboxStanalone/modals/CreateUserStandaloneModal";
import { useModalToggle } from "~shared/hooks/useModalToggle";

import { NewsMessage, messages } from "./news.mock";

import "./NewsPage.scss";

const headerBarItems = [
  { label: "Messages", path: PATHS.newsSection(NEWS_SECTIONS.messages) },
  { label: "Attachments", path: PATHS.newsSection(NEWS_SECTIONS.attachments) },
  { label: "Links", path: PATHS.newsSection(NEWS_SECTIONS.links) },
  { label: "Participants", path: PATHS.newsSection(NEWS_SECTIONS.participants) },
  { label: "Details", path: PATHS.newsSection(NEWS_SECTIONS.details) },
  { label: "Audit trail", path: PATHS.newsSection(NEWS_SECTIONS.auditTrail) },
];

function MessageCard({ message }: { message: NewsMessage }) {
  return (
    <div className="adobe-news__message">
      <RegularText size={1} color="grey-5" className="adobe-news__meta">
        {message.meta}
      </RegularText>
      <Card testId={`news-card-${message.id}`}>
        <BoldText size={4} className="adobe-news__title">
          {message.title}
        </BoldText>
        <RegularText className="adobe-news__intro">{message.intro}</RegularText>
        {message.bulletsTitle ? (
          <BoldText className="adobe-news__bullets-title">{message.bulletsTitle}</BoldText>
        ) : null}
        <ul className="adobe-news__bullets">
          {message.bullets.map((bullet, index) => (
            <li key={index}>
              {bullet.lead ? <strong>{bullet.lead} </strong> : null}
              {bullet.text}
            </li>
          ))}
        </ul>
        <RegularText size={1} className="adobe-news__link">
          For more detailed information, visit:{" "}
          <a href={message.link} target="_top" rel="noreferrer">
            {message.link}
          </a>
        </RegularText>
      </Card>
    </div>
  );
}

export function NewsMessagesSection() {
  return (
    <div className="adobe-news__messages">
      {messages.map((message) => (
        <MessageCard key={message.id} message={message} />
      ))}
    </div>
  );
}

export function NewsPage() {
  // Example 1 — standalone modal: rendered in this app, toggled with useModalToggle.
  const createUser = useModalToggle();
  // Example 2 — entry modal: ask the MPT host to mount the create-entitlement
  // modal bundle by id (only opens when running inside the host).
  const { open } = useMPTModal();

  return (
    <Card className="adobe-news">
      <header className="adobe-news__header">
        <span className="adobe-news__brand">A</span>
        <div className="adobe-news__header-text">
          <RegularText size={1} color="grey-5">
            Chat CHT-4130-7598
          </RegularText>
          <BoldText size={4}>Adobe news</BoldText>
        </div>
      </header>

      <Navigation>
        <Navigation.HeaderBar items={headerBarItems}>
          <Navigation.HeaderBar.Actions>
            <Button type="primary" onClick={() => createUser.open()}>
              Create user (standalone modal)
            </Button>
            <Button
              onClick={() =>
                open("finops.admin.create-entitlement-modal", { context: {}, onClose: () => {} })
              }
            >
              Create entitlement (entry modal)
            </Button>
            <Button>Edit</Button>
          </Navigation.HeaderBar.Actions>
        </Navigation.HeaderBar>
        <Navigation.Content>
          <Outlet />
        </Navigation.Content>
      </Navigation>

      <CreateUserStandaloneModal isOpen={createUser.isOpen} onClose={createUser.close} />
    </Card>
  );
}
