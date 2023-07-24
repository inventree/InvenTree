import { Container, Flex, Text } from '@mantine/core';
import _ from 'lodash';
import React from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveReactGridLayout = WidthProvider(Responsive);

const compactType = 'vertical';
const currentBreakpoint = 'lg';

function ToolBoxItem({ item, onTakeItem }: { item: any; onTakeItem: any }) {
  return (
    <Container
      style={{ border: '1px solid' }}
      bg={'green'}
      className="toolbox__items__item"
      onClick={onTakeItem.bind(undefined, item)}
      m={0}
    >
      {item.i}
    </Container>
  );
}

function ToolBox({ items, onTakeItem }: { items: any[]; onTakeItem: any }) {
  return (
    <Container className="toolbox" p={0} m={0}>
      <Text>Toolbox</Text>
      <Flex justify="flex-start" align="flex-start" direction="row" wrap="wrap">
        {items.map((item) => (
          <ToolBoxItem key={item.i} item={item} onTakeItem={onTakeItem} />
        ))}
      </Flex>
    </Container>
  );
}

function Item({
  item,
  onPutItem,
  children
}: {
  item: any;
  onPutItem: any;
  children: any;
}) {
  return (
    <div key={item.i}>
      <div className="hide-button" onClick={onPutItem.bind(item)}>
        &times;
      </div>
      <span className="text">{item.i}</span>
      {children}
    </div>
  );
}

export default class ToolboxLayout extends React.Component {
  static defaultProps = {
    className: 'layout',
    rowHeight: 30,
    cols: { lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 },
    initialLayout: generateLayout()
  };

  state = {
    mounted: false,
    layouts: { lg: this.props.initialLayout },
    toolbox: { lg: [] }
  };

  componentDidMount() {
    this.setState({ mounted: true });
  }

  generateDOM() {
    return _.map(this.state.layouts[currentBreakpoint], (l) => {
      return (
        <Container key={l.i} bg={'gray'}>
          <div className="hide-button" onClick={this.onPutItem.bind(this, l)}>
            &times;
          </div>
          <hr />
          <span className="text">{l.i}</span>
        </Container>
      );
    });
  }

  onTakeItem = (item: any) => {
    this.setState((prevState) => ({
      toolbox: {
        ...prevState.toolbox,
        [currentBreakpoint]: prevState.toolbox[currentBreakpoint].filter(
          ({ i }) => i !== item.i
        )
      },
      layouts: {
        ...prevState.layouts,
        [currentBreakpoint]: [...prevState.layouts[currentBreakpoint], item]
      }
    }));
  };

  onPutItem = (item: any) => {
    this.setState((prevState) => {
      return {
        toolbox: {
          ...prevState.toolbox,
          [currentBreakpoint]: [
            ...(prevState.toolbox[currentBreakpoint] || []),
            item
          ]
        },
        layouts: {
          ...prevState.layouts,
          [currentBreakpoint]: prevState.layouts[currentBreakpoint].filter(
            ({ i }) => i !== item.i
          )
        }
      };
    });
  };

  onNewLayout = () => {
    this.setState({
      layouts: { lg: generateLayout() }
    });
  };

  render() {
    return (
      <div>
        <ToolBox
          items={this.state.toolbox[currentBreakpoint] || []}
          onTakeItem={this.onTakeItem}
        />

        <ResponsiveReactGridLayout
          {...this.props}
          layouts={this.state.layouts}
          measureBeforeMount={false}
          useCSSTransforms={this.state.mounted}
          compactType={compactType}
          preventCollision={!compactType}
        >
          {this.generateDOM()}
        </ResponsiveReactGridLayout>
      </div>
    );
  }
}

function generateLayout() {
  return _.map(_.range(0, 25), function (item, i) {
    var y = Math.ceil(Math.random() * 4) + 1;
    return {
      x: (_.random(0, 5) * 2) % 12,
      y: Math.floor(i / 6) * y,
      w: 2,
      h: y,
      i: i.toString()
    };
  });
}
