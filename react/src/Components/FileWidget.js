import { List, Tag } from 'antd';
import { FileOutlined } from '@ant-design/icons';
import React from 'react';

class FileWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
        files: [],
        files_tags: {}
    };
    this.files = {};
    this.getFilesList();
  }

  getFilesList() {
    fetch('/api/files/search')
      .then(response => {
        response.json().then(data => (this.setState({ files: data })))
      })
  }

  getFileTags(file) {
    fetch('/api/tags/file/' + file)
      .then(response => {
        response.json().then(data => {
          let tags = [];
          data.map(tag => tags.push(<Tag>{tag[0]}:{tag[1]}</Tag>));
          this.files[file] = tags;
          this.setState({ files_tags: {...this.state.files_tags, [file]: tags} })
        })
      })
  }

  fileClicked(file) {
    this.getFileTags(file.innerText);
  }
  
  render() {
    return (
      <div>
          <List
            loading={this.state.files == null}
            header={<span>Files</span>}
            bordered
            dataSource={this.state.files}
            renderItem={item =>
              <List.Item onClick={(e) => this.fileClicked(e.target)}>
                <List.Item.Meta
                  avatar={<FileOutlined />}
                  title={item}
                  description={this.state.files_tags[item]}
                />
              </List.Item>
            }
          />
      </div>
    );
  }
}

export default FileWidget;