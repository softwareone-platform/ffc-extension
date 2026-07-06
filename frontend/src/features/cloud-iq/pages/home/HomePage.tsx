import { Button } from "@swo/design-system/button";
import { Card } from "@swo/design-system/card";
import { Icon } from "@swo/design-system/icon";
import { BoldText, RegularText } from "@swo/design-system/text";
import { Tiles } from "@swo/design-system/tiles";

import heroIllustration from "~assets/sample-header.png";
import { hero, jumpBackIn, whatsNew } from "./home.mock";

import "./HomePage.scss";

export function HomePage() {
  return (
    <div className="cloud-iq-home">
      <Card className="cloud-iq-home__hero" testId="cloud-iq-hero">
        <div className="cloud-iq-home__hero-content">
          <RegularText size={1} color="grey-5">
            {hero.greeting}
          </RegularText>
          <BoldText size={4} className="cloud-iq-home__hero-title">
            {hero.title}
          </BoldText>
          {hero.body.split("\n").map((line, index) => (
            <RegularText key={index} className="cloud-iq-home__hero-body">
              {line}
            </RegularText>
          ))}
          <div className="cloud-iq-home__hero-actions">
            <Button type="primary">Edit</Button>
            <Button type="secondary">Read More</Button>
          </div>
        </div>
        <img className="cloud-iq-home__hero-illustration" src={heroIllustration} alt="" />
      </Card>

      <section className="cloud-iq-home__section">
        <BoldText size={4}>Jump Back In</BoldText>
        <Tiles className="cloud-iq-home__tiles">
          {jumpBackIn.map((tile) => (
            <Tiles.Tile
              key={tile.id}
              url="#"
              title={tile.title}
              subtitle=""
              icon={<Icon name={tile.icon} size={24} />}
            />
          ))}
        </Tiles>
      </section>

      <section className="cloud-iq-home__section">
        <BoldText size={4}>What's New</BoldText>
        <div className="cloud-iq-home__whats-new">
          {whatsNew.map((item) => (
            <Card key={item.id} testId={`whats-new-${item.id}`}>
              <img className="cloud-iq-home__whats-new-image" src={item.image} alt="" />
              <RegularText size={1} color="grey-5">
                {item.category}
              </RegularText>
              <BoldText className="cloud-iq-home__whats-new-title">{item.title}</BoldText>
              <RegularText size={1}>{item.excerpt}</RegularText>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
