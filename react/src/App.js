import './App.css';
import React from 'react';
import FileWidget from './Components/FileWidget';
import TagTreeWidget from './Components/TagTreeWidget';
import { Row, Col } from 'antd';
import 'antd/dist/antd.min.css';

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      list: [],
    };
  }

  addTagToSearch(tag) {
    let list = [...this.state.list, tag.key];
    this.setState({list});
  }

  render() {
    return (
      <div className="App">
        <Row>
          <Col span={4}>
            <TagTreeWidget addTagToSearch={(e) => this.addTagToSearch(e)} />
          </Col>
          <Col span={20}>
            <FileWidget />
          </Col>
        </Row>
      </div>
    );
  }
}

export default App;