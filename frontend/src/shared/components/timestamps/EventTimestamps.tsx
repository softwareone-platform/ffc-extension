import { useCallback, useState } from "react";

import { Avatar } from "@swo/design-system/avatar";
import { Button } from "@swo/design-system/button";
import { Ellipsis } from "@swo/design-system/ellipsis";
import { EntityReference } from "@swo/design-system/entity-reference";
import { Icon } from "@swo/design-system/icon";
import { NO_VALUE, useLocalisation } from "@swo/design-system/utils";

import styles from "./EventTimestamps.module.scss";

export type EntityEvent = {
  name: string;
  by?: {
    id: string;
    name: string;
  };
  at?: Date;
};

export interface TimestampsProps {
  events: EntityEvent[];
  columnNames?: string[];
  componentTitle?: string;
  isToHideUrl?: boolean;
  denseMode?: boolean;
}

export function EventTimestamps({ events, columnNames = [], componentTitle }: TimestampsProps) {
  const { formatDate, formatTime } = useLocalisation();
  const [expanded, setExpanded] = useState(false);
  const toggleExpanded = useCallback(() => setExpanded(!expanded), [expanded]);

  if (!events.length) {
    return <></>;
  }

  return (
    <>
      {componentTitle && <h3 className={styles["title"]}>{componentTitle}</h3>}
      <div className={styles["data"]}>
        <div className={styles["headers"]}>
          <div className={styles["name"]}>{columnNames[0]}</div>
          <div className={styles["by"]}>{columnNames[1]}</div>
          <div className={styles["at"]}>{columnNames[2]}</div>
          <div className={styles["button-container"]}>
            <Button onClick={toggleExpanded} type="text">
              <Icon
                name={expanded ? "arrow_up_keyboard" : "arrow_down_keyboard"}
                type="outlined"
                size={24}
              />
            </Button>
          </div>
        </div>
        {(expanded ? events : [events[0]]).map((event, i) => (
          <div key={i} className={styles["row"]}>
            <div className={styles["name"]}>
              <Ellipsis>{event.name}</Ellipsis>
            </div>
            <div className={styles["by"]}>
              {event.by?.id ? (
                <EntityReference
                  primaryContent={event.by.name}
                  secondaryContent={event.by.id}
                  icon={
                    <Avatar
                      text={(event.by?.id as string) || NO_VALUE}
                      size={32}
                      isToUseJdenticon={true}
                    />
                  }
                />
              ) : (
                NO_VALUE
              )}
            </div>
            <div className={styles["at"]}>
              {event.at ? (
                <EntityReference
                  primaryContent={formatDate(event.at)}
                  secondaryContent={formatTime(event.at)}
                />
              ) : (
                NO_VALUE
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
