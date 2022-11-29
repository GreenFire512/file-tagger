import { List } from 'antd';
import React from 'react';

class FileWidget extends React.Component {
  // constructor(props) {
  //   super(props);
  //   this.state = {
  //       list: []
  //   };
  // }
  
  render() {
    return (
      <div>
        <List
          loading={this.props.list == null}
          header={<div>Tag Search</div>}
          bordered
          dataSource={this.props.list}
          renderItem={item => <List.Item>{item}</List.Item>}
        />
      </div>
    );
  }
}

export default FileWidget;