import { FileOutlined } from '@ant-design/icons';
import { List, Tag } from 'antd';
import { useState } from 'react';

export default function FileWidget() {
  const [files, setFiles] = useState([])
  const [filesTags, setFilesTags] = useState([])

  function getFilesList() {
    fetch('/api/files/search')
      .then(response => {
        response.json().then(data => (this.setState({ files: data })))
      })
  }

  function getFileTags(file) {
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

  function fileClicked(file) {
    getFileTags(file.innerText);
  }
  
  return (
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
  );
}