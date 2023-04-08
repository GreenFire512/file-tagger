import { Col, Row } from 'antd';
import FileWidget from './FileWidget/FileWidget';
import TagTreeWidget from './TagTreeWidget';

export default function App() {

  // function addTagToSearch(tag) {
  //   let list = [...this.state.list, tag.key];
  //   this.setState({list});
  // }

  return (
    <div className="App">
      <Row>
        <Col span={4}>
          <TagTreeWidget />
        </Col>
        <Col span={20}>
          <FileWidget />
        </Col>
      </Row>
    </div>
  );
}